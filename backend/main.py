"""
Vocalis Backend - Simplified Version
Medical prescription assistant with LLM-powered information extraction
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uvicorn
import requests
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
import sqlite3
import uuid
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vocalis-backend")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
ollama_available = False

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "prescriptions.db")

# Current session ID
current_session_id = None

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
# DATABASE FUNCTIONS
# ============================================================================

def init_db():
    """Initialize SQLite database with prescriptions table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id TEXT PRIMARY KEY,
            patient_name TEXT,
            patient_age TEXT,
            diagnosis TEXT,
            medication TEXT,
            dosage TEXT,
            duration TEXT,
            special_instructions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")


def create_new_session() -> str:
    """Create new prescription session and return session ID"""
    global current_session_id
    session_id = str(uuid.uuid4())
    current_session_id = session_id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prescriptions (id) VALUES (?)
    ''', (session_id,))
    conn.commit()
    conn.close()
    logger.info(f"New session created: {session_id}")
    return session_id


def get_session_data() -> PrescriptionData:
    """Get session data from database"""
    global current_session_id
    if not current_session_id:
        create_new_session()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT patient_name, patient_age, diagnosis, medication, dosage, duration, special_instructions
        FROM prescriptions WHERE id = ?
    ''', (current_session_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return PrescriptionData(
            patientName=row['patient_name'],
            patientAge=row['patient_age'],
            diagnosis=row['diagnosis'],
            medication=row['medication'],
            dosage=row['dosage'],
            duration=row['duration'],
            specialInstructions=row['special_instructions']
        )
    return PrescriptionData()


def update_session_data(data: PrescriptionData) -> None:
    """Update session data in database"""
    global current_session_id
    if not current_session_id:
        create_new_session()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE prescriptions SET
            patient_name = ?,
            patient_age = ?,
            diagnosis = ?,
            medication = ?,
            dosage = ?,
            duration = ?,
            special_instructions = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.patientName,
        data.patientAge,
        data.diagnosis,
        data.medication,
        data.dosage,
        data.duration,
        data.specialInstructions,
        current_session_id
    ))
    conn.commit()
    conn.close()
    logger.info(f"Session {current_session_id} updated")


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


def call_ollama(prompt: str, max_tokens: int = 100) -> str:
    """Call Ollama API and return the response"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,
            "top_p": 0.9,
        }
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return ""


def extract_data_from_message(text: str, current_data: PrescriptionData) -> PrescriptionData:
    """Extract prescription data using Ollama with clear prompt"""
    if not ollama_available:
        logger.warning("Ollama not available, skipping extraction")
        return current_data

    logger.info(f"Extracting from text: {text}")

    # Clear prompt for Mistral - no placeholders!
    extraction_prompt = (
        f"Extrait ces 7 informations du texte:\n{text}\n\n"
        f"Retourne SEULEMENT:\n"
        f"Nom: \n"
        f"Age: \n"
        f"Diagnostic: \n"
        f"Medicament: \n"
        f"Dosage: \n"
        f"Duree: \n"
        f"Instructions: \n\n"
        f"Complete chaque ligne avec la valeur extraite du texte. Si absent, laisse vide."
    )

    try:
        response = call_ollama(extraction_prompt, max_tokens=150)
        logger.info(f"Ollama response:\n{response}")

        # Parse line by line with more specific matching
        for line in response.split('\n'):
            line = line.strip()
            if ':' not in line:
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            key = parts[0].strip().lower()
            value = parts[1].strip()

            # Skip empty/placeholder values
            if not value or value.lower().strip() in ['vide', 'absent', 'aucun', 'none', 'none (since no', '', '[]', 'n/a']:
                continue

            # Map to fields using exact key matching - ALWAYS UPDATE
            if key == 'nom':
                current_data.patientName = value
                logger.info(f"Extracted name: {value}")
            elif key == 'age':
                current_data.patientAge = value
                logger.info(f"Extracted age: {value}")
            elif key == 'diagnostic':
                current_data.diagnosis = value
                logger.info(f"Extracted diagnosis: {value}")
            elif key == 'medicament':
                current_data.medication = value
                logger.info(f"Extracted medication: {value}")
            elif key == 'dosage' or key == 'dosologie' or key == 'posologie':
                current_data.dosage = value
                logger.info(f"Extracted dosage: {value}")
            elif key == 'duree' or key == 'durée' or key == 'duration':
                current_data.duration = value
                logger.info(f"Extracted duration: {value}")
            elif key == 'instructions':
                current_data.specialInstructions = value
                logger.info(f"Extracted instructions: {value}")

    except Exception as e:
        logger.error(f"Extraction error: {e}")

    return current_data


def generate_response(user_message: str, prescription_data: PrescriptionData) -> str:
    """Generate conversational response using Ollama"""
    if not ollama_available:
        return "Erreur: Ollama non disponible"

    collected = prescription_data.format_display()
    missing = ", ".join(prescription_data.get_missing_fields()) or "Aucun"

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Informations collectees:\n{collected}\n\n"
        f"Informations manquantes:\n{missing}\n\n"
        f"Message utilisateur: {user_message}\n\n"
        f"Reponds en francais. Confirme les infos recues et demande les infos manquantes."
    )

    try:
        response = call_ollama(prompt, max_tokens=256)
        return response if response else "Je n'ai pas pu générer une réponse."
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return f"Erreur: {str(e)}"


# ============================================================================
# STARTUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and check Ollama at startup"""
    global ollama_available, current_session_id

    # Initialize database
    init_db()
    current_session_id = None

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


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
    logger.info(f"Chat request: {request.message[:50]}...")

    if not ollama_available:
        raise HTTPException(
            status_code=503,
            detail="Ollama n'est pas disponible. Veuillez démarrer Ollama."
        )

    try:
        # Get current session data
        current_data = get_session_data()

        # Extract information from user message
        current_data = extract_data_from_message(request.message, current_data)

        # Save updated data
        update_session_data(current_data)

        # Generate response
        response_text = generate_response(request.message, current_data)

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


@app.post("/api/generate-pdf")
async def generate_pdf(request: GeneratePDFRequest):
    """Generate PDF from collected prescription data"""
    logger.info("PDF generation request")

    try:
        # Get current session data
        current_data = get_session_data()

        # Check if complete
        if not current_data.is_complete():
            missing = ", ".join(current_data.get_missing_fields())
            raise HTTPException(
                status_code=400,
                detail=f"Donnees incomples: {missing}"
            )

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

        # Signature
        if request.signature_base64:
            try:
                if "," in request.signature_base64:
                    sig_data = request.signature_base64.split(",")[1]
                else:
                    sig_data = request.signature_base64

                img_bytes = base64.b64decode(sig_data)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(img_bytes)
                    tmp_path = tmp.name

                pdf.cell(0, 5, "Signature:", ln=True)
                pdf.image(tmp_path, w=50)
                os.remove(tmp_path)

            except Exception as e:
                logger.error(f"Signature error: {e}")
                pdf.cell(0, 5, "[Signature Error]", ln=True)

        # Save and return
        filename = f"ordonnance_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)

        logger.info(f"PDF generated: {filename}")
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    except Exception as e:
        logger.exception("PDF generation error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session():
    """Reset the current session and create new one"""
    global current_session_id
    current_session_id = create_new_session()
    return {"status": "ok", "message": "Session reset", "session_id": current_session_id}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
