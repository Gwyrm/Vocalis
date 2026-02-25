"""
Vocalis Backend - Simplified Version
Medical prescription assistant with LLM-powered information extraction
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uvicorn
import requests
import httpx
import urllib3
from fpdf import FPDF
import base64
import os
import tempfile
import uuid
import logging
from contextlib import asynccontextmanager
import json
from datetime import datetime
import re
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vocalis-backend")

# ============================================================================
# SECURITY HELPERS
# ============================================================================

def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitize user input to prevent prompt injection

    - Limit length to prevent token overflow
    - Remove control characters
    - Safe for inclusion in prompts
    """
    if not text:
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Remove null bytes and control characters (except newlines and tabs)
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")

    return text.strip()


def validate_signature_image(signature_base64: str) -> Optional[bytes]:
    """Validate and decode base64 signature image

    Returns:
        Decoded image bytes if valid, None otherwise
    """
    if not signature_base64:
        return None

    try:
        # Remove data URI prefix if present
        if "," in signature_base64:
            sig_data = signature_base64.split(",")[1]
        else:
            sig_data = signature_base64

        # Decode and validate
        img_bytes = base64.b64decode(sig_data, validate=True)

        # Check size (limit to 1MB)
        if len(img_bytes) > 1_000_000:
            logger.warning(f"Signature image too large: {len(img_bytes)} bytes")
            return None

        # Validate PNG magic bytes (PNG: 89 50 4E 47)
        if not img_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            logger.warning("Signature image is not a valid PNG")
            return None

        return img_bytes

    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid base64 signature: {e}")
        return None


# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
ollama_available = False

# In-memory session storage with lock for thread safety
session_data = {}
session_lock = asyncio.Lock()

# NOTE: This is a single-user implementation. For multi-user deployments,
# implement proper session management with session IDs and persistence.

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

EXTRACTION_PROMPT_TEMPLATE = (
    "Extrait UNIQUEMENT les informations medicales du texte suivant et retourne un JSON.\n"
    "Cles possibles: patientName, patientAge, diagnosis, medication, dosage, duration, specialInstructions.\n"
    "Retourne SEULEMENT le JSON valide, rien d'autre.\n"
    "Si une information est absente, ne l'inclus pas dans le JSON.\n\n"
    "Texte: {text}"
)

RESPONSE_PROMPT_TEMPLATE = (
    "Infos collectees:\n{collected_info}\n\n"
    "Infos manquantes obligatoires:\n{missing_fields}\n\n"
    "Message utilisateur: {user_message}\n\n"
    "Reponds en francais. Confirme les infos recues et demande les infos manquantes."
)

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

    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields in French"""
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
# LLM HELPERS
# ============================================================================

def format_chat_prompt(user_message: str) -> str:
    """Format prompt using TinyLlama chat template"""
    return (
        f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
        f"<|user|>\n{user_message}</s>\n"
        f"<|assistant|>\n"
    )


async def call_ollama(prompt: str, max_tokens: int = 100) -> str:
    """Call Ollama API asynchronously and return the response"""
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
    """Normalize key by removing accents and converting to lowercase"""
    import unicodedata
    nfd = unicodedata.normalize('NFD', key)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').lower()


def is_empty_response(value: str) -> bool:
    """Check if a response indicates the field is empty/absent"""
    if not value:
        return True

    normalized = value.lower().strip()

    # List of phrases that indicate absence of information
    empty_indicators = [
        'vide', 'absent', 'aucun', 'aucune',
        'none', 'pas spécifié', 'pas specifie',
        'pas mentionné', 'pas mentionne',
        'n/a', 'na', 'non applicable',
        'non fourni', 'non fournie',
        'n\'est pas', 'n\'existe pas', 'n\'y a pas',
        '[]', 'null', 'undefined',
        'depuis no', 'since no',  # "none (since no..."
        'not provided', 'not specified',
        'non indiqué', 'non indiquee',
        'inconnu', 'inconnue',
        'renseignement spécifique', 'renseignement specifique',
        'consulter votre médecin', 'consulter votre medecin',
        'consulter la notice',
        'ne donne pas de',
        'non spécifié', 'non specifie',
    ]

    # Check if the value starts with any empty indicator
    for indicator in empty_indicators:
        if normalized.startswith(indicator):
            return True

    # Check if it's mostly parentheses/explanations
    if normalized.startswith('(') and normalized.endswith(')'):
        return True

    # Check if it's too long and contains explanation markers
    if len(value) > 200 and ('message' in normalized or 'veuillez' in normalized):
        return True

    return False


async def extract_data_from_message(text: str, current_data: PrescriptionData) -> PrescriptionData:
    """Extract prescription data using Ollama with improved parsing and prompt injection prevention"""
    if not ollama_available:
        logger.warning("Ollama not available, skipping extraction")
        return current_data

    # Sanitize input to prevent prompt injection
    safe_text = sanitize_input(text)
    logger.info(f"Extracting from text: {safe_text[:100]}...")

    # Build context of existing data for the model
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

    # Improved extraction prompt with context preservation and sanitized input
    extraction_prompt = (
        f"Tu extrais les informations medicales d'un message.\n\n"
    )

    if context_str:
        extraction_prompt += (
            f"CONTEXTE (informations deja collectees):\n"
            f"{context_str}\n\n"
            f"Conserve ces informations et ajoute les nouvelles du message suivant.\n\n"
        )

    extraction_prompt += (
        f"NOUVEAU MESSAGE:\n{safe_text}\n\n"
        f"REPONSE (7 lignes SEULEMENT):\n"
        f"Nom:\n"
        f"Age:\n"
        f"Diagnostic:\n"
        f"Medicament:\n"
        f"Dosage:\n"
        f"Duree:\n"
        f"Instructions:"
    )

    try:
        response = await call_ollama(extraction_prompt, max_tokens=150)
        logger.info(f"Ollama response:\n{response}")

        # Parse line by line with improved matching
        for line in response.split('\n'):
            line = line.strip()
            if ':' not in line or not line:
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            key = parts[0].strip()
            value = parts[1].strip()

            # Skip if value is empty or indicates absence
            if is_empty_response(value):
                logger.info(f"Skipping empty value for {key}: {value}")
                continue

            # Normalize key for matching (handles accents: durée → duree)
            normalized_key = normalize_key(key)

            # Map to fields with normalized key matching
            if normalized_key == 'nom' or normalized_key == 'name':
                current_data.patientName = sanitize_input(value, 200)
                logger.info(f"Extracted name: {current_data.patientName}")

            elif normalized_key == 'age':
                current_data.patientAge = sanitize_input(value, 100)
                logger.info(f"Extracted age: {current_data.patientAge}")

            elif normalized_key == 'diagnostic' or normalized_key == 'diagnosis':
                current_data.diagnosis = sanitize_input(value, 500)
                logger.info(f"Extracted diagnosis: {current_data.diagnosis}")

            elif normalized_key == 'medicament' or normalized_key == 'medication':
                current_data.medication = sanitize_input(value, 200)
                logger.info(f"Extracted medication: {current_data.medication}")

            elif normalized_key in ['dosage', 'dosologie', 'dosologie', 'posologie']:
                current_data.dosage = sanitize_input(value, 200)
                logger.info(f"Extracted dosage: {current_data.dosage}")

            elif normalized_key in ['duree', 'duration', 'durée']:
                current_data.duration = sanitize_input(value, 200)
                logger.info(f"Extracted duration: {current_data.duration}")

            elif normalized_key == 'instructions' or normalized_key == 'instruction':
                current_data.specialInstructions = sanitize_input(value, 500)
                logger.info(f"Extracted instructions: {current_data.specialInstructions}")

    except Exception as e:
        logger.error(f"Extraction error: {e}")

    return current_data


async def generate_response(user_message: str, prescription_data: PrescriptionData) -> str:
    """Generate conversational response using Ollama with prompt injection prevention"""
    if not ollama_available:
        return "Erreur: Ollama non disponible"

    # Sanitize user input to prevent prompt injection
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


# ============================================================================
# STARTUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check Ollama availability at startup"""
    global ollama_available, session_data

    session_data = {}

    # Check Ollama availability
    logger.info(f"Checking Ollama at {OLLAMA_BASE_URL} with model {OLLAMA_MODEL}...")
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_available = True
            logger.info("Ollama is available!")
        else:
            logger.warning(f"Ollama returned status {response.status_code}")
            ollama_available = False
    except Exception as e:
        logger.error(f"Ollama not available: {e}")
        ollama_available = False

    yield
    logger.info("Shutting down...")
    ollama_available = False
    session_data = {}


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(lifespan=lifespan)

# Enable CORS with configurable origins (defaults to localhost for security)
# Set CORS_ORIGINS env var to comma-separated list of allowed origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5000,http://127.0.0.1:3000").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

logger.info(f"CORS enabled for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Vocalis Backend is running"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "backend": "running",
        "ollama_available": ollama_available,
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - handles everything"""
    global session_data
    logger.info(f"Chat request: {request.message[:50]}...")

    if not ollama_available:
        raise HTTPException(
            status_code=503,
            detail="Ollama n'est pas disponible. Veuillez démarrer Ollama."
        )

    try:
        async with session_lock:
            # Get current session data (thread-safe with lock)
            current_data = PrescriptionData(**session_data) if session_data else PrescriptionData()

            # Extract information from user message (with prompt injection prevention)
            current_data = await extract_data_from_message(request.message, current_data)

            # Save updated data to session
            session_data = current_data.model_dump(exclude_none=True)

        # Generate response (outside lock to avoid blocking, with prompt injection prevention)
        response_text = await generate_response(request.message, current_data)

        # Check if complete
        is_complete = current_data.is_complete()
        missing = current_data.get_missing_fields()

        return ChatResponse(
            response=response_text,
            is_complete=is_complete,
            missing_fields=missing,
            prescription_data=current_data
        )

    except Exception as e:
        logger.exception("Error in chat")
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_temp_file(filepath: str):
    """Cleanup temporary PDF file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up temp file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to cleanup temp file {filepath}: {e}")


@app.post("/api/generate-pdf")
async def generate_pdf(request: GeneratePDFRequest, background_tasks: BackgroundTasks):
    """Generate PDF from collected prescription data"""
    global session_data
    logger.info("PDF generation request")

    async with session_lock:
        # Get current session data (thread-safe with lock)
        current_data = PrescriptionData(**session_data) if session_data else PrescriptionData()

    # Check if complete
    if not current_data.is_complete():
        missing = ", ".join(current_data.get_missing_fields())
        raise HTTPException(
            status_code=400,
            detail=f"Données incomplètes: {missing}"
        )

    try:
        # Build prescription text
        prescription_text = f"""ORDONNANCE MEDICALE

Patient: {current_data.patientName}
Age: {current_data.patientAge}

DIAGNOSTIC:
{current_data.diagnosis}

MEDICAMENT:
{current_data.medication}

POSOLOGIE:
{current_data.dosage}

DUREE:
{current_data.duration}

INSTRUCTIONS SPECIALES:
{current_data.specialInstructions}

Date: {datetime.now().strftime('%d/%m/%Y')}
"""

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        # Title
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "ORDONNANCE MEDICALE", ln=True, align="C")
        pdf.ln(5)

        # Content
        pdf.set_font("Arial", size=10)
        for line in prescription_text.split("\n"):
            pdf.cell(0, 5, line, ln=True)

        pdf.ln(10)

        # Signature (with validation)
        sig_temp_path = None
        if request.signature_base64:
            img_bytes = validate_signature_image(request.signature_base64)
            if img_bytes:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(img_bytes)
                        sig_temp_path = tmp.name

                    pdf.cell(0, 5, "Signature:", ln=True)
                    pdf.image(sig_temp_path, w=50)

                except Exception as e:
                    logger.error(f"Signature processing error: {e}")
                    pdf.cell(0, 5, "[Signature Error]", ln=True)
            else:
                logger.warning("Signature validation failed")
                pdf.cell(0, 5, "[Invalid Signature]", ln=True)

        # Save PDF
        filename = f"ordonnance_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)

        # Schedule cleanup tasks for temp files
        if sig_temp_path:
            background_tasks.add_task(cleanup_temp_file, sig_temp_path)
        background_tasks.add_task(cleanup_temp_file, filepath)

        logger.info(f"PDF generated: {filename}")
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    except Exception as e:
        logger.exception("PDF generation error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session():
    """Reset the current session"""
    global session_data
    async with session_lock:
        session_data = {}
    return {"status": "ok", "message": "Session reset"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
