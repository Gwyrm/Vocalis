"""LLM utilities for prescription extraction and chat"""

import base64
import httpx
import logging
import tempfile
import os
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger("vocalis-backend")

# ============================================================================
# PROMPTS
# ============================================================================

SYSTEM_PROMPT = (
    "Tu es un assistant medical specialise dans la redaction d'ordonnances.\n\n"
    "LANGUE: FRANCAIS UNIQUEMENT. Jamais d'espagnol, anglais ou autre langue.\n\n"
    "Informations OBLIGATOIRES pour une ordonnance:\n"
    "1. Nom du patient\n"
    "2. Age ou date de naissance\n"
    "3. Diagnostic\n"
    "4. Medicament\n"
    "5. Posologie (dosage et frequence)\n"
    "6. Duree du traitement\n"
    "7. Instructions speciales\n\n"
    "Sois clair, concis et professionnel. Reponds EN FRANCAIS uniquement."
)

# ============================================================================
# SECURITY HELPERS
# ============================================================================

def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitize user input to prevent prompt injection"""
    if not text:
        return ""

    text = text[:max_length]
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")
    return text.strip()


def validate_signature_image(signature_base64: str) -> Optional[bytes]:
    """Validate and decode base64 signature image"""
    if not signature_base64:
        return None

    try:
        if "," in signature_base64:
            sig_data = signature_base64.split(",")[1]
        else:
            sig_data = signature_base64

        img_bytes = base64.b64decode(sig_data, validate=True)

        if len(img_bytes) > 1_000_000:
            logger.warning(f"Signature image too large: {len(img_bytes)} bytes")
            return None

        if not img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            logger.warning("Signature image is not a valid PNG")
            return None

        return img_bytes

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid base64 signature: {e}")
        return None


def cleanup_temp_file(filepath: str):
    """Cleanup temporary PDF file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up temp file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to cleanup temp file {filepath}: {e}")


# ============================================================================
# DATA MODELS
# ============================================================================

class PrescriptionData(BaseModel):
    """Prescription information"""
    patientName: Optional[str] = None
    patientAge: Optional[str] = None
    diagnosis: Optional[str] = None
    medication: Optional[str] = None
    dosage: Optional[str] = None
    duration: Optional[str] = None
    specialInstructions: Optional[str] = None
    discovered_allergies: Optional[List[str]] = None
    discovered_conditions: Optional[List[str]] = None

    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields"""
        required = [
            ('patientName', 'Nom du patient'),
            ('patientAge', 'Age/Date de naissance'),
            ('diagnosis', 'Diagnostic'),
            ('medication', 'Medicament'),
            ('dosage', 'Posologie'),
            ('duration', 'Duree du traitement'),
            ('specialInstructions', 'Instructions speciales'),
        ]
        missing = []
        for field, label in required:
            if not getattr(self, field):
                missing.append(label)
        return missing

    def is_complete(self) -> bool:
        """Check if all required fields are present"""
        return len(self.get_missing_fields()) == 0

    def format_display(self) -> str:
        """Format for display"""
        lines = []
        if self.patientName:
            lines.append(f"- Nom: {self.patientName}")
        if self.patientAge:
            lines.append(f"- Age: {self.patientAge}")
        if self.diagnosis:
            lines.append(f"- Diagnostic: {self.diagnosis}")
        if self.medication:
            lines.append(f"- Medicament: {self.medication}")
        if self.dosage:
            lines.append(f"- Posologie: {self.dosage}")
        if self.duration:
            lines.append(f"- Duree: {self.duration}")
        if self.specialInstructions:
            lines.append(f"- Instructions: {self.specialInstructions}")
        return "\n".join(lines) if lines else "Aucune info"


class ChatRequest(BaseModel):
    """User message"""
    message: str


class ChatResponse(BaseModel):
    """Response with status"""
    response: str
    is_complete: bool
    missing_fields: List[str]
    prescription_data: PrescriptionData


class GeneratePDFRequest(BaseModel):
    """Request to generate PDF"""
    signature_base64: str


# ============================================================================
# LLM FUNCTIONS
# ============================================================================

async def call_ollama(prompt: str, max_tokens: int = 100) -> str:
    """Call Ollama API asynchronously"""
    import os
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,
            "top_p": 0.9,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return ""


def normalize_key(key: str) -> str:
    """Normalize key by removing accents"""
    import unicodedata
    nfd = unicodedata.normalize('NFD', key)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').lower()


def is_empty_response(value: str) -> bool:
    """Check if response indicates field is empty"""
    if not value:
        return True

    normalized = value.lower().strip()

    empty_indicators = [
        'vide', 'absent', 'aucun', 'aucune',
        'none', 'pas spécifié', 'pas specifie',
        'pas mentionné', 'pas mentionne',
        'n/a', 'na', 'non applicable',
        'non fourni', 'non fournie',
        'n\'est pas', 'n\'existe pas', 'n\'y a pas',
        '[]', 'null', 'undefined',
        'depuis no', 'since no',
        'not provided', 'not specified',
        'non indiqué', 'non indiquee',
        'inconnu', 'inconnue',
        'renseignement spécifique', 'renseignement specifique',
        'consulter votre médecin', 'consulter votre medecin',
        'consulter la notice',
        'ne donne pas de',
        'non spécifié', 'non specifie',
    ]

    for indicator in empty_indicators:
        if normalized.startswith(indicator):
            return True

    if normalized.startswith('(') and normalized.endswith(')'):
        return True

    if len(value) > 200 and ('message' in normalized or 'veuillez' in normalized):
        return True

    return False


async def extract_data_from_message(text: str, current_data: PrescriptionData) -> PrescriptionData:
    """Extract prescription data using Ollama"""
    # Check if Ollama is available
    import os
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_available = response.status_code == 200
    except:
        ollama_available = False

    if not ollama_available:
        logger.warning("Ollama not available, skipping extraction")
        return current_data

    safe_text = sanitize_input(text)
    logger.info(f"Extracting from text: {safe_text[:100]}...")

    existing_context = []
    if current_data.patientName:
        existing_context.append(f"Patient actuel: {sanitize_input(current_data.patientName, 200)}")
    if current_data.patientAge:
        existing_context.append(f"Age connu: {sanitize_input(current_data.patientAge, 100)}")
    if current_data.diagnosis:
        existing_context.append(f"Diagnostic connu: {sanitize_input(current_data.diagnosis, 200)}")
    if current_data.medication:
        existing_context.append(f"Medicament connu: {sanitize_input(current_data.medication, 200)}")

    context_str = "\n".join(existing_context) if existing_context else ""

    extraction_prompt = f"Tu extrais les informations medicales d'un message.\n\n"

    if context_str:
        extraction_prompt += (
            f"CONTEXTE (informations deja collectees):\n"
            f"{context_str}\n\n"
            f"Conserve ces informations et ajoute les nouvelles du message suivant.\n\n"
        )

    extraction_prompt += (
        f"NOUVEAU MESSAGE:\n{safe_text}\n\n"
        f"REPONSE (9 lignes SEULEMENT, format exact):\n"
        f"Nom:\nAge:\nDiagnostic:\nMedicament:\nDosage:\nDuree:\nInstructions:\nAllergies:\nConditions:"
    )

    try:
        response = await call_ollama(extraction_prompt, max_tokens=150)
        logger.info(f"Ollama response:\n{response}")

        for line in response.split('\n'):
            line = line.strip()
            if ':' not in line or not line:
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            key = parts[0].strip()
            value = parts[1].strip()

            if is_empty_response(value):
                logger.info(f"Skipping empty value for {key}: {value}")
                continue

            normalized_key = normalize_key(key)

            if normalized_key == 'nom' or normalized_key == 'name':
                current_data.patientName = sanitize_input(value, 200)
            elif normalized_key == 'age':
                current_data.patientAge = sanitize_input(value, 100)
            elif normalized_key == 'diagnostic' or normalized_key == 'diagnosis':
                current_data.diagnosis = sanitize_input(value, 500)
            elif normalized_key == 'medicament' or normalized_key == 'medication':
                current_data.medication = sanitize_input(value, 200)
            elif normalized_key in ['dosage', 'dosologie', 'posologie']:
                current_data.dosage = sanitize_input(value, 200)
            elif normalized_key in ['duree', 'duration', 'durée']:
                current_data.duration = sanitize_input(value, 200)
            elif normalized_key == 'instructions' or normalized_key == 'instruction':
                current_data.specialInstructions = sanitize_input(value, 500)
            elif normalized_key in ['allergies', 'allergie']:
                # Store allergies - will be added to patient record
                allergies_str = sanitize_input(value, 500)
                if not hasattr(current_data, 'discovered_allergies'):
                    current_data.discovered_allergies = []
                if allergies_str and allergies_str.lower() not in ['aucune', 'none', 'no', 'non']:
                    current_data.discovered_allergies = [allergies_str]
                    logger.info(f"Discovered allergies: {allergies_str}")
            elif normalized_key in ['conditions', 'condition']:
                # Store chronic conditions - will be added to patient record
                conditions_str = sanitize_input(value, 500)
                if not hasattr(current_data, 'discovered_conditions'):
                    current_data.discovered_conditions = []
                if conditions_str and conditions_str.lower() not in ['aucune', 'none', 'no', 'non']:
                    current_data.discovered_conditions = [conditions_str]
                    logger.info(f"Discovered conditions: {conditions_str}")

    except Exception as e:
        logger.error(f"Extraction error: {e}")

    return current_data


async def generate_response(user_message: str, prescription_data: PrescriptionData) -> str:
    """Generate conversational response using Ollama"""
    import os
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        ollama_available = response.status_code == 200
    except:
        ollama_available = False

    if not ollama_available:
        return "Erreur: Ollama non disponible"

    safe_user_message = sanitize_input(user_message, 2000)
    collected = prescription_data.format_display()
    missing = ", ".join(prescription_data.get_missing_fields()) or "Aucun"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Informations collectees:\n{collected}\n\n"
        f"Informations manquantes:\n{missing}\n\n"
        f"Message utilisateur: {safe_user_message}\n\n"
        f"Reponds en francais. Confirme les infos recues et demande les infos manquantes."
    )

    try:
        response = await call_ollama(prompt, max_tokens=256)
        return response if response else "Je n'ai pas pu générer une réponse."
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return f"Erreur: {str(e)}"


def format_chat_prompt(user_message: str) -> str:
    """Format prompt using TinyLlama chat template"""
    return (
        f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
        f"<|user|>\n{user_message}</s>\n"
        f"<|assistant|>\n"
    )
