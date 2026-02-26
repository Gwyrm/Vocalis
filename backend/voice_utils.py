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

    # Check for suspicious dosage values (e.g., "00mg", "0mg")
    import re
    dosage_num = re.search(r'(\d+)', dosage)
    if dosage_num:
        num_value = int(dosage_num.group(1))
        if num_value == 0:
            errors.append({
                "type": "invalid_value",
                "message": f"Dosage value cannot be zero: {dosage}",
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


async def parse_prescription_text(text: str) -> Dict:
    """
    Parse prescription text using LLM (Large Language Model) for intelligent extraction.
    Handles flexible natural language formats including:
    - "amoxicilline 500mg trois fois par jour, 7 jours"
    - "amoxicilline (500mg) trois fois par jour"
    - "Prescrire amoxicilline, dosage 500mg, pour 7 jours, trois fois par jour"
    - Any natural language variation

    Returns dict with extracted fields:
    - patient_name
    - medication
    - dosage
    - duration
    - special_instructions
    """
    import json

    prescription = {
        "patient_name": None,
        "medication": None,
        "dosage": None,
        "duration": None,
        "special_instructions": None,
    }

    # Create a structured extraction prompt
    prompt = f"""Tu es un assistant medical spécialisé dans l'extraction d'informations d'ordonnances.

Extrais les informations suivantes du texte ci-dessous et retourne UNIQUEMENT du JSON valide (pas de texte supplémentaire):

Texte de l'ordonnance:
"{text}"

Retourne EXACTEMENT ce format JSON (remplace par null si non trouvé):
{{
    "medication": "nom du médicament",
    "dosage": "dosage avec unité (ex: 500mg)",
    "duration": "durée du traitement (ex: 7 jours)",
    "special_instructions": "fréquence et instructions spéciales (ex: trois fois par jour avec repas)",
    "patient_name": "nom du patient si mentionné"
}}

Règles importantes:
1. Le dosage DOIT contenir un nombre valide (pas 00, pas 0)
2. Accepte les variations: mg, g, ml, mcg, gouttes, etc.
3. Pour la durée: accepte jours, semaines, mois
4. Retourne UNIQUEMENT du JSON, aucun texte avant ou après
5. Si un champ n'est pas trouvé, utilise null"""

    try:
        response = await call_ollama(prompt, max_tokens=200)

        # Try to extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            parsed_json = json.loads(json_str)

            # Map JSON response to prescription dict
            prescription["medication"] = parsed_json.get("medication")
            prescription["dosage"] = parsed_json.get("dosage")
            prescription["duration"] = parsed_json.get("duration")
            prescription["special_instructions"] = parsed_json.get("special_instructions")
            prescription["patient_name"] = parsed_json.get("patient_name")

            logger.info(f"LLM parsed prescription: medication={prescription['medication']}, dosage={prescription['dosage']}")
        else:
            logger.warning(f"Failed to extract JSON from LLM response: {response}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error from LLM response: {e}")
    except Exception as e:
        logger.error(f"Error calling LLM for prescription parsing: {e}")

    return prescription


async def structure_prescription_data(
    transcribed_text: str,
    patient_id: str,
    patient_age: int,
    patient_conditions: List[str],
    patient_allergies: List[str],
    current_medications: List[str]
) -> Tuple[Dict, Dict]:
    """
    Structure raw prescription text into validated data using LLM parsing.

    Returns:
        Tuple of (structured_prescription, validation_result)
    """
    # Parse the text using LLM
    parsed = await parse_prescription_text(transcribed_text)

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
