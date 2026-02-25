"""Voice and AI utilities for Vocalis"""

import logging
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import whisper

logger = logging.getLogger("vocalis-backend")

# Load Whisper model (small model, ~461MB)
WHISPER_MODEL = whisper.load_model("small", device="cpu")


def transcribe_audio(audio_file_path: str, language: str = "fr") -> Tuple[str, float]:
    """
    Transcribe audio file to text using Whisper

    Args:
        audio_file_path: Path to audio file (mp3, wav, m4a, etc.)
        language: Language code (e.g., "fr" for French, "en" for English)

    Returns:
        Tuple of (transcribed_text, confidence_score)
    """
    try:
        result = WHISPER_MODEL.transcribe(
            audio_file_path,
            language=language,
            verbose=False,
        )

        text = result["text"].strip()
        confidence = result.get("confidence", 0.95)

        logger.info(f"Audio transcribed: {len(text)} characters, confidence: {confidence:.2%}")

        return text, confidence

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise


def validate_medication(
    medication_name: str,
    dosage: str,
    patient_age: int,
    patient_conditions: List[str] = None,
    patient_allergies: List[str] = None,
    current_medications: List[str] = None
) -> Dict:
    """
    Validate medication against patient data

    Args:
        medication_name: Name of medication
        dosage: Dosage string (e.g., "5mg twice daily")
        patient_age: Patient age in years
        patient_conditions: List of chronic conditions
        patient_allergies: List of known allergies
        current_medications: List of current medications

    Returns:
        Validation result with warnings and errors
    """
    patient_conditions = patient_conditions or []
    patient_allergies = patient_allergies or []
    current_medications = current_medications or []

    warnings = []
    errors = []

    # Check for allergy
    if medication_name.lower() in [med.lower() for med in patient_allergies]:
        errors.append({
            "type": "allergy_warning",
            "message": f"Patient is allergic to {medication_name}",
            "field": "medication"
        })

    # Check age appropriateness (basic validation)
    if "pediatric" in medication_name.lower() and patient_age > 18:
        warnings.append({
            "type": "age_warning",
            "message": "Pediatric medication for adult patient",
            "severity": "medium"
        })

    # Check dosage format
    if not any(char.isdigit() for char in dosage):
        errors.append({
            "type": "invalid_value",
            "message": "Dosage must contain a numeric value",
            "field": "dosage"
        })

    # Check for common interactions (simplified)
    interaction_pairs = [
        ("warfarin", "aspirin"),
        ("metformin", "alcohol"),
        ("lisinopril", "potassium"),
    ]

    for med1, med2 in interaction_pairs:
        if medication_name.lower() == med1 or medication_name.lower() == med2:
            for current_med in current_medications:
                if current_med.lower() == med2 or current_med.lower() == med1:
                    warnings.append({
                        "type": "interaction_warning",
                        "message": f"Possible interaction between {medication_name} and {current_med}",
                        "severity": "high"
                    })

    return {
        "valid": len(errors) == 0,
        "warnings": warnings,
        "errors": errors,
        "confidence": 0.85 if warnings else 0.95
    }


def parse_prescription_text(text: str) -> Dict:
    """
    Parse prescription text using pattern matching and basic NLP

    Returns dict with extracted fields:
    - patient_name
    - medication
    - dosage
    - duration
    - special_instructions
    """
    prescription = {
        "patient_name": None,
        "medication": None,
        "dosage": None,
        "duration": None,
        "special_instructions": None,
    }

    lines = text.lower().split("\n")

    # Simple pattern matching
    for line in lines:
        if "patient" in line or "nom" in line or "name" in line:
            # Extract patient name (simplified)
            words = line.split()
            if len(words) > 1:
                prescription["patient_name"] = " ".join(words[-2:])

        if any(med in line for med in ["medication", "medicament", "drug", "medicine"]):
            # Extract medication name
            words = line.split(":")
            if len(words) > 1:
                prescription["medication"] = words[-1].strip()

        if "dosage" in line or "dose" in line or "posologie" in line:
            words = line.split(":")
            if len(words) > 1:
                prescription["dosage"] = words[-1].strip()

        if "duration" in line or "duree" in line or "jours" in line or "days" in line:
            words = line.split(":")
            if len(words) > 1:
                prescription["duration"] = words[-1].strip()

        if any(instr in line for instr in ["instruction", "note", "special", "with", "without"]):
            prescription["special_instructions"] = line.strip()

    return prescription


def structure_prescription_data(
    transcribed_text: str,
    patient_id: str,
    patient_age: int,
    patient_conditions: List[str],
    patient_allergies: List[str],
    current_medications: List[str]
) -> Tuple[Dict, Dict]:
    """
    Structure raw prescription text into validated data

    Returns:
        Tuple of (structured_prescription, validation_result)
    """
    # Parse the text
    parsed = parse_prescription_text(transcribed_text)

    # Validate medication if present
    validation = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "confidence": 0.85
    }

    if parsed.get("medication"):
        med_validation = validate_medication(
            parsed["medication"],
            parsed.get("dosage", ""),
            patient_age,
            patient_conditions,
            patient_allergies,
            current_medications
        )
        validation = med_validation

    # Check all required fields
    required_fields = ["medication", "dosage"]
    for field in required_fields:
        if not parsed.get(field):
            validation["errors"].append({
                "type": "missing_field",
                "message": f"Missing required field: {field}",
                "field": field
            })
            validation["valid"] = False

    structured = {
        "patient_id": patient_id,
        "medication": parsed.get("medication"),
        "dosage": parsed.get("dosage"),
        "duration": parsed.get("duration", "30 days"),  # Default
        "special_instructions": parsed.get("special_instructions"),
        "created_at": datetime.utcnow().isoformat(),
        "source": "voice"
    }

    return structured, validation
