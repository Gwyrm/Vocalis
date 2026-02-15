from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
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

SYSTEM_PROMPT = (
    "Tu es un assistant medical specialise dans la redaction d'ordonnances. "
    "Tu collectes des informations sur le patient de maniere conversationnelle et naturelle. "
    "Quand l'utilisateur te fournit une information, tu l'extrais et la stockes. "
    "Si des informations requises manquent, demande-les poliment en fonction du contexte. "
    "Les informations requises sont: nom du patient, age/date de naissance, diagnostic, "
    "medicament, posologie, duree du traitement, instructions speciales. "
    "Reponds en francais, de maniere professionnelle et empathique."
)

COLLECTION_PROMPT_TEMPLATE = (
    "Tu collectes des informations medicales pour une ordonnance. "
    "L'utilisateur a fourni les informations suivantes:\n{collected_data}\n"
    "Le dernier message de l'utilisateur est: {user_message}\n"
    "Les informations manquantes requises sont: {missing_fields}\n"
    "Reponds en francais. Extrait les nouvelles informations du dernier message et "
    "demande poliment les informations manquantes. Sois concis et empathique."
)

PRESCRIPTION_GENERATION_PROMPT_TEMPLATE = (
    "Redige une ordonnance medicale professionnelle en francais basee sur les informations suivantes:\n"
    "- Nom du patient: {patient_name}\n"
    "- Age/Date de naissance: {patient_age}\n"
    "- Diagnostic: {diagnosis}\n"
    "- Medicament: {medication}\n"
    "- Posologie: {dosage}\n"
    "- Duree du traitement: {duration}\n"
    "- Instructions speciales: {special_instructions}\n"
    "Fournis une ordonnance bien formatee, professionnelle et complete."
)

# TinyLlama chat template tokens (built dynamically to avoid markup issues)
_LP = "<"
_RP = ">"
_PIPE = "|"
SYS_TAG = f"{_LP}{_PIPE}system{_PIPE}{_RP}"
USER_TAG = f"{_LP}{_PIPE}user{_PIPE}{_RP}"
ASST_TAG = f"{_LP}{_PIPE}assistant{_PIPE}{_RP}"
EOS_TAG = "</s>"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup, release at shutdown."""
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
    logger.info("Shutting down, releasing model...")
    llm = None


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class ChatRequest(BaseModel):
    message: str


class PrescriptionRequest(BaseModel):
    content: str
    signature_base64: str


class PrescriptionData(BaseModel):
    """Data model for prescription information"""
    patientName: Optional[str] = Field(None, description="Patient full name")
    patientAge: Optional[str] = Field(None, description="Patient age or date of birth")
    diagnosis: Optional[str] = Field(None, description="Medical diagnosis")
    medication: Optional[str] = Field(None, description="Medication name")
    dosage: Optional[str] = Field(None, description="Dosage and frequency")
    duration: Optional[str] = Field(None, description="Duration of treatment")
    specialInstructions: Optional[str] = Field(None, description="Special instructions")

    def get_missing_required_fields(self) -> List[str]:
        """Return list of missing required fields in French"""
        required = [
            ('patientName', 'Nom du patient'),
            ('patientAge', 'Âge/Date de naissance'),
            ('diagnosis', 'Diagnostic'),
            ('medication', 'Médicament'),
            ('dosage', 'Posologie'),
            ('duration', 'Durée du traitement'),
            ('specialInstructions', 'Instructions spéciales'),
        ]
        return [label for field, label in required if not getattr(self, field)]

    def is_complete(self) -> bool:
        """Check if all required fields are present"""
        return len(self.get_missing_required_fields()) == 0

    def format_for_display(self) -> str:
        """Format collected data for display"""
        lines = []
        if self.patientName:
            lines.append(f"• Nom du patient: {self.patientName}")
        if self.patientAge:
            lines.append(f"• Âge/DOB: {self.patientAge}")
        if self.diagnosis:
            lines.append(f"• Diagnostic: {self.diagnosis}")
        if self.medication:
            lines.append(f"• Médicament: {self.medication}")
        if self.dosage:
            lines.append(f"• Posologie: {self.dosage}")
        if self.duration:
            lines.append(f"• Durée: {self.duration}")
        if self.specialInstructions:
            lines.append(f"• Instructions: {self.specialInstructions}")
        return "\n".join(lines) if lines else "Aucune information collectée"


class CollectInfoRequest(BaseModel):
    """Request to collect prescription information"""
    currentData: PrescriptionData
    userInput: str


class CollectInfoResponse(BaseModel):
    """Response from information collection"""
    status: str  # "needs_more_info" | "complete"
    missingFields: List[str]
    message: str  # AI response to send to user
    collectedData: PrescriptionData


class GeneratePrescriptionRequest(BaseModel):
    """Request to generate prescription from complete data"""
    data: PrescriptionData


class GeneratePrescriptionResponse(BaseModel):
    """Response with generated prescription"""
    prescription: str  # Formatted prescription text


def format_chat_prompt(user_message: str) -> str:
    """Format prompt using TinyLlama chat template."""
    return (
        f"{SYS_TAG}\n{SYSTEM_PROMPT}{EOS_TAG}\n"
        f"{USER_TAG}\n{user_message}{EOS_TAG}\n"
        f"{ASST_TAG}\n"
    )


def extract_prescription_data_from_message(
    text: str, current_data: PrescriptionData
) -> PrescriptionData:
    """
    Uses AI to intelligently extract medical information from user input.
    Updates provided PrescriptionData with new information.
    Preserves existing fields.
    """
    if llm is None:
        return current_data

    extraction_prompt = (
        f"{SYS_TAG}\nTu es un expert en extraction d'informations medicales. "
        f"Extrait les informations medicales du texte fourni et retourne-les en JSON. "
        f"Les cles JSON doivent etre: patientName, patientAge, diagnosis, medication, dosage, duration, specialInstructions. "
        f"Ne retourne que les cles pour les informations trouvees. {EOS_TAG}\n"
        f"{USER_TAG}\nTexte a analyser: {text}{EOS_TAG}\n"
        f"{ASST_TAG}\n"
    )

    try:
        output = llm(
            extraction_prompt,
            max_tokens=256,
            temperature=0.3,
            top_p=0.9,
            stop=[EOS_TAG],
            echo=False
        )
        response_text = output["choices"][0]["text"].strip()

        # Parse JSON response
        try:
            extracted = json.loads(response_text)
            # Update current_data with extracted information
            if "patientName" in extracted and extracted["patientName"]:
                current_data.patientName = extracted["patientName"]
            if "patientAge" in extracted and extracted["patientAge"]:
                current_data.patientAge = extracted["patientAge"]
            if "diagnosis" in extracted and extracted["diagnosis"]:
                current_data.diagnosis = extracted["diagnosis"]
            if "medication" in extracted and extracted["medication"]:
                current_data.medication = extracted["medication"]
            if "dosage" in extracted and extracted["dosage"]:
                current_data.dosage = extracted["dosage"]
            if "duration" in extracted and extracted["duration"]:
                current_data.duration = extracted["duration"]
            if "specialInstructions" in extracted and extracted["specialInstructions"]:
                current_data.specialInstructions = extracted["specialInstructions"]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from extraction: {response_text}")

    except Exception as e:
        logger.error(f"Error extracting prescription data: {e}")

    return current_data


def build_info_request_prompt(
    current_data: PrescriptionData, user_message: str
) -> str:
    """
    Creates formatted prompt for AI to guide information collection.
    Identifies missing required fields and asks naturally for missing information.
    """
    collected_info = current_data.format_for_display()
    missing = current_data.get_missing_required_fields()
    missing_str = ", ".join(missing) if missing else "Aucun"

    prompt = COLLECTION_PROMPT_TEMPLATE.format(
        collected_data=collected_info,
        user_message=user_message,
        missing_fields=missing_str
    )

    return (
        f"{SYS_TAG}\n{SYSTEM_PROMPT}{EOS_TAG}\n"
        f"{USER_TAG}\n{prompt}{EOS_TAG}\n"
        f"{ASST_TAG}\n"
    )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    logger.info(f"Received chat request: {request.message[:50]}...")

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Le modele n'est pas encore charge. Veuillez patienter."
        )

    try:
        prompt = format_chat_prompt(request.message)
        logger.info("Generating response...")

        output = llm(
            prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            stop=[EOS_TAG, ASST_TAG],
            echo=False
        )

        response_text = output["choices"][0]["text"].strip()
        logger.info(f"Generated response ({len(response_text)} chars)")
        return {"response": response_text}

    except Exception as e:
        logger.exception("Error during chat generation")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de generation: {str(e)}"
        )


@app.post("/api/collect-prescription-info", response_model=CollectInfoResponse)
async def collect_prescription_info(request: CollectInfoRequest):
    """
    Collect prescription information from user input.
    Extracts data, validates completeness, and guides toward complete information.
    """
    logger.info(f"Received collect-info request: {request.userInput[:50]}...")

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Le modele n'est pas encore charge. Veuillez patienter."
        )

    try:
        # Extract new information from user input
        updated_data = extract_prescription_data_from_message(
            request.userInput, request.currentData
        )

        # Check if complete
        is_complete = updated_data.is_complete()
        missing_fields = updated_data.get_missing_required_fields()

        # Generate AI guidance message
        guidance_prompt = build_info_request_prompt(updated_data, request.userInput)
        logger.info("Generating guidance message...")

        output = llm(
            guidance_prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=[EOS_TAG],
            echo=False
        )

        message = output["choices"][0]["text"].strip()
        logger.info(f"Generated guidance message ({len(message)} chars)")

        return CollectInfoResponse(
            status="complete" if is_complete else "needs_more_info",
            missingFields=missing_fields,
            message=message,
            collectedData=updated_data
        )

    except Exception as e:
        logger.exception("Error collecting prescription info")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de collecte: {str(e)}"
        )


@app.post("/api/generate-prescription", response_model=GeneratePrescriptionResponse)
async def generate_prescription(request: GeneratePrescriptionRequest):
    """
    Generate a professionally formatted prescription from complete data.
    """
    logger.info("Received generate-prescription request")

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Le modele n'est pas encore charge. Veuillez patienter."
        )

    # Validate that data is complete
    if not request.data.is_complete():
        missing = request.data.get_missing_required_fields()
        raise HTTPException(
            status_code=400,
            detail=f"Donnees incomples. Manquant: {', '.join(missing)}"
        )

    try:
        # Build prescription generation prompt
        gen_prompt = PRESCRIPTION_GENERATION_PROMPT_TEMPLATE.format(
            patient_name=request.data.patientName,
            patient_age=request.data.patientAge,
            diagnosis=request.data.diagnosis,
            medication=request.data.medication,
            dosage=request.data.dosage,
            duration=request.data.duration,
            special_instructions=request.data.specialInstructions
        )

        full_prompt = (
            f"{SYS_TAG}\n{SYSTEM_PROMPT}{EOS_TAG}\n"
            f"{USER_TAG}\n{gen_prompt}{EOS_TAG}\n"
            f"{ASST_TAG}\n"
        )

        logger.info("Generating prescription...")
        output = llm(
            full_prompt,
            max_tokens=512,
            temperature=0.5,
            top_p=0.9,
            stop=[EOS_TAG],
            echo=False
        )

        prescription_text = output["choices"][0]["text"].strip()
        logger.info(f"Generated prescription ({len(prescription_text)} chars)")

        return GeneratePrescriptionResponse(prescription=prescription_text)

    except Exception as e:
        logger.exception("Error generating prescription")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de generation: {str(e)}"
        )


@app.post("/api/generate-pdf")
async def generate_pdf(request: PrescriptionRequest):
    logger.info("Received PDF generation request")
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="Ordonnance Medicale", ln=1, align="C")
        pdf.ln(10)

        # Add Content
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=request.content)
        pdf.ln(20)

        # Handle Signature
        if request.signature_base64:
            try:
                if "," in request.signature_base64:
                    signature_data = request.signature_base64.split(",")[1]
                else:
                    signature_data = request.signature_base64

                img_data = base64.b64decode(signature_data)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    tmp_img.write(img_data)
                    tmp_img_path = tmp_img.name

                pdf.image(tmp_img_path, w=50)
                os.remove(tmp_img_path)

            except Exception as e:
                logger.error(f"Error processing signature: {e}")
                pdf.cell(200, 10, txt="[Signature Error]", ln=1)

        # Output PDF to temporary file
        filename = f"prescription_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)

        logger.info(f"Successfully generated PDF: {filename}")
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    except Exception as e:
        logger.exception("Error during PDF generation")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
