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
# SESSION STORAGE (In-memory)
# ============================================================================

# Store prescription data per session (could use sessionID if needed)
prescription_storage: Dict[str, PrescriptionData] = {}

def get_session_data() -> PrescriptionData:
    """Get or create session data"""
    session_id = "default"  # Simple session ID (could be per-user)
    if session_id not in prescription_storage:
        prescription_storage[session_id] = PrescriptionData()
    return prescription_storage[session_id]


def update_session_data(data: PrescriptionData) -> None:
    """Update session data"""
    session_id = "default"
    prescription_storage[session_id] = data


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

    prompt = (
        f"<|system|>\nTu es un expert medical. Extrait les infos du texte et retourne JSON.\n"
        f"Cles: patientName, patientAge, diagnosis, medication, dosage, duration, specialInstructions.\n"
        f"Retourne SEULEMENT le JSON valide.</s>\n"
        f"<|user|>\nTexte: {text}</s>\n"
        f"<|assistant|>\n"
    )

    try:
        output = llm(
            prompt,
            max_tokens=200,
            temperature=0.1,
            top_p=0.9,
            stop=["</s>"],
            echo=False
        )
        response = output["choices"][0]["text"].strip()

        # Extract JSON
        if "{" in response:
            json_str = response[response.find("{"):response.rfind("}")+1]
            extracted = json.loads(json_str)

            # Update data
            for key in ["patientName", "patientAge", "diagnosis", "medication",
                       "dosage", "duration", "specialInstructions"]:
                if key in extracted and extracted[key]:
                    value = str(extracted[key]).strip()
                    if value and value.lower() not in ["none", "null"]:
                        setattr(current_data, key, value)
                        logger.info(f"Extracted {key}: {value}")

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
    """Load model at startup, release at shutdown"""
    global llm
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
    """Reset the current session (clear all data)"""
    session_id = "default"
    prescription_storage[session_id] = PrescriptionData()
    return {"status": "ok", "message": "Session reset"}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("main_v2:app", host="0.0.0.0", port=8080, reload=True)
