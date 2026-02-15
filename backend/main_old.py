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
    "Tu es un assistant medical specialise dans la redaction d'ordonnances.\n\n"
    "LANGUE: Tu DOIS repondre UNIQUEMENT en FRANCAIS. Jamais en espagnol, anglais ou autre langue.\n\n"
    "Ton role:\n"
    "1. Collecter les informations du patient de maniere conversationnelle\n"
    "2. Confirmer chaque information recue\n"
    "3. Demander les informations manquantes\n"
    "4. Rester professionnel et empathique\n\n"
    "Informations OBLIGATOIRES:\n"
    "- Nom du patient\n"
    "- Age ou date de naissance\n"
    "- Diagnostic\n"
    "- Medicament\n"
    "- Posologie (dosage et frequence)\n"
    "- Duree du traitement\n"
    "- Instructions speciales (si applicables)\n\n"
    "REGLE IMPORTANTE: Reponds UNIQUEMENT en francais. Sois clair et concis."
)

COLLECTION_PROMPT_TEMPLATE = (
    "Tu es un assistant medical qui collecte les informations pour une ordonnance.\n\n"
    "LANGUE OBLIGATOIRE: FRANCAIS UNIQUEMENT - Ne reponds JAMAIS en espagnol, anglais ou autre langue.\n\n"
    "Informations collectees jusqu'a present:\n{collected_data}\n\n"
    "Dernier message du patient: {user_message}\n\n"
    "Informations encore manquantes: {missing_fields}\n\n"
    "Instructions (EN FRANCAIS):\n"
    "1. Confirme les informations que tu as compris du dernier message\n"
    "2. Demande poliment les informations manquantes\n"
    "3. Sois concis et clair\n"
    "4. REPONDRE UNIQUEMENT EN FRANCAIS - C'est TRES IMPORTANT\n"
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

    def toJson(self) -> dict:
        """Alias for model_dump for compatibility"""
        return self.model_dump()

    @classmethod
    def fromJson(cls, data: dict) -> "PrescriptionData":
        """Alias for model_validate for compatibility"""
        return cls.model_validate(data)

    def copyWith(self, **kwargs) -> "PrescriptionData":
        """Create a copy with updated fields"""
        return self.model_copy(update=kwargs)


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


def ensure_french_response(text: str) -> str:
    """
    Ensure response is in French. If it detects Spanish or other languages,
    requests a French translation from the LLM.
    """
    # Spanish indicators
    spanish_patterns = [
        "¿", "¡",  # Spanish punctuation
        "hola", "buenos", "gracias", "por favor",
        "me llamo", "tengo años", "cual es",
        "el diagnostico", "la medicina"
    ]

    text_lower = text.lower()
    spanish_count = sum(1 for pattern in spanish_patterns if pattern in text_lower)

    # If more than 2 Spanish patterns found, ask for French version
    if spanish_count > 2:
        logger.warning(f"Detected Spanish response, requesting French translation")
        if llm is not None:
            try:
                translation_prompt = (
                    f"{SYS_TAG}\nTu es un traducteur. Traduis ce texte de l'espagnol au francais.\n"
                    f"Reponds UNIQUEMENT avec la traduction francaise, rien d'autre.{EOS_TAG}\n"
                    f"{USER_TAG}\nTexte espagnol: {text}{EOS_TAG}\n"
                    f"{ASST_TAG}\n"
                )
                output = llm(
                    translation_prompt,
                    max_tokens=256,
                    temperature=0.3,
                    stop=[EOS_TAG],
                    echo=False
                )
                translated = output["choices"][0]["text"].strip()
                logger.info(f"Translated to French: {translated[:100]}")
                return translated
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                return text

    return text


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

    # Improved extraction prompt - more direct and simpler
    extraction_prompt = (
        f"{SYS_TAG}\nTu es un assistant medical. "
        f"Extrait UNIQUEMENT les informations medicales du message et retourne JSON. "
        f"Cles possibles: patientName (nom patient), patientAge (age/DOB), diagnosis (diagnostic), "
        f"medication (medicament), dosage (posologie), duration (duree), specialInstructions (instructions). "
        f"Retourne SEULEMENT le JSON, rien d'autre.{EOS_TAG}\n"
        f"{USER_TAG}\nExtraire du texte: {text}{EOS_TAG}\n"
        f"{ASST_TAG}\n"
    )

    try:
        output = llm(
            extraction_prompt,
            max_tokens=200,
            temperature=0.1,  # Lower temperature for more consistent extraction
            top_p=0.9,
            stop=[EOS_TAG, "```"],
            echo=False
        )
        response_text = output["choices"][0]["text"].strip()

        # Try to extract JSON from response (handle markdown code blocks)
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        response_text = response_text.strip()

        # Parse JSON response
        if response_text.startswith("{"):
            try:
                extracted = json.loads(response_text)
                logger.info(f"Extracted data: {extracted}")

                # Update current_data with extracted information
                for key in ["patientName", "patientAge", "diagnosis", "medication",
                           "dosage", "duration", "specialInstructions"]:
                    if key in extracted and extracted[key]:
                        value = str(extracted[key]).strip()
                        if value and value.lower() not in ["none", "null", "n/a"]:
                            setattr(current_data, key, value)
                            logger.info(f"Set {key} = {value}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {response_text[:100]} - {e}")
        else:
            logger.warning(f"Response is not JSON: {response_text[:100]}")

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

    full_prompt = (
        f"{SYS_TAG}\n{SYSTEM_PROMPT}{EOS_TAG}\n"
        f"{USER_TAG}\n{prompt}{EOS_TAG}\n"
        f"{ASST_TAG}\n"
    )

    logger.debug(f"Full prompt:\n{full_prompt[:500]}...")

    return full_prompt


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

        # Ensure response is in French
        response_text = ensure_french_response(response_text)

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

        # Ensure response is in French
        message = ensure_french_response(message)

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

        # Ensure prescription is in French
        prescription_text = ensure_french_response(prescription_text)

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
