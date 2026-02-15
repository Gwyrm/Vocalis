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
from llama_cpp import Llama
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vocalis-backend")

# Global model reference
llm = None

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
)

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


def extract_data_from_message(text: str, current_data: PrescriptionData) -> PrescriptionData:
    """Extract prescription data from user message using LLM"""
    if llm is None:
        return current_data

    # Build prompt for LLM to extract medical information
    prompt = (
        f"<|system|>\nTu es un expert medical specialise dans l'extraction de donnees.\n"
        f"Extrais les informations medicales du texte et retourne UNIQUEMENT du JSON valide.\n"
        f"Format JSON attendu avec les clés: patientName, patientAge, diagnosis, medication, dosage, duration, specialInstructions\n"
        f"Utilise null pour les champs manquants. Ne retourne QUE le JSON, rien d'autre.</s>\n"
        f"<|user|>\nTexte: {text}</s>\n"
        f"<|assistant|>\n"
    )

    try:
        output = llm(
            prompt,
            max_tokens=300,
            temperature=0.1,
            top_p=0.9,
            stop=["</s>"],
            echo=False
        )
        response = output["choices"][0]["text"].strip()
        logger.info(f"LLM extraction response: {response[:200]}")

        # Extract JSON from response
        if "{" in response and "}" in response:
            json_str = response[response.find("{"):response.rfind("}")+1]
            extracted = json.loads(json_str)

            # Update current_data with extracted values
            for key in ["patientName", "patientAge", "diagnosis", "medication",
                       "dosage", "duration", "specialInstructions"]:
                if key in extracted and extracted[key]:
                    value = str(extracted[key]).strip()
                    if value and value.lower() not in ["none", "null", "n/a", ""]:
                        setattr(current_data, key, value)
                        logger.info(f"Extracted {key}: {value}")
        else:
            logger.warning(f"No JSON found in LLM response")

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
    except Exception as e:
        logger.error(f"Extraction error: {e}")

    return current_data


def generate_response(user_message: str, prescription_data: PrescriptionData) -> str:
    """Generate response using LLM"""
    if llm is None:
        return "Erreur: Modele non charge"

    collected = prescription_data.format_display()
    missing = ", ".join(prescription_data.get_missing_fields()) or "Aucun"

    prompt = RESPONSE_PROMPT_TEMPLATE.format(
        collected_info=collected,
        missing_fields=missing,
        user_message=user_message
    )

    full_prompt = (
        f"<|system|>\n{SYSTEM_PROMPT}</s>\n"
        f"<|user|>\n{prompt}</s>\n"
        f"<|assistant|>\n"
    )

    try:
        output = llm(
            full_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["</s>"],
            echo=False
        )
        response = output["choices"][0]["text"].strip()
        return response
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return f"Erreur: {str(e)}"


# ============================================================================
# STARTUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and load model at startup"""
    global llm, current_session_id

    # Initialize database
    init_db()
    current_session_id = None

    # Load model
    logger.info(f"Loading model from {MODEL_PATH}...")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,
            verbose=False
        )
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    yield
    logger.info("Shutting down...")
    llm = None


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
        "model_loaded": llm is not None,
        "model_path": MODEL_PATH
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - handles everything"""
    logger.info(f"Chat request: {request.message[:50]}...")

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Le modele n'est pas encore charge."
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
    uvicorn.run("main_v2:app", host="0.0.0.0", port=8080, reload=True)
