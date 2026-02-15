#!/usr/bin/env python3
"""Script to generate main.py with special tokens."""

SYS = "<" + "|system|" + ">"
USR = "<" + "|user|" + ">"
AST = "<" + "|assistant|" + ">"
EOS = "<" + "/s" + ">"

content = f'''from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from llama_cpp import Llama
from fpdf import FPDF
import base64
import os
import tempfile
import uuid
import logging
from contextlib import asynccontextmanager

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
    "Tu es un assistant medical. Tu aides les medecins a rediger des ordonnances medicales. "
    "Reponds en francais, de maniere claire et professionnelle. "
    "Fournis des prescriptions structurees avec le nom du medicament, la posologie et la duree du traitement."
)

SYS_TAG = "{SYS}"
USER_TAG = "{USR}"
ASST_TAG = "{AST}"
EOS_TAG = "{EOS}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup, release at shutdown."""
    global llm
    logger.info(f"Loading model from {{MODEL_PATH}}...")
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
        logger.error(f"Failed to load model: {{e}}")
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
    return {{"status": "ok", "message": "Vocalis Backend is running"}}


@app.get("/api/health")
async def health_check():
    return {{
        "status": "ok",
        "backend": "running",
        "model_loaded": llm is not None,
        "model_path": MODEL_PATH
    }}


class ChatRequest(BaseModel):
    message: str


class PrescriptionRequest(BaseModel):
    content: str
    signature_base64: str


def format_chat_prompt(user_message: str) -> str:
    """Format prompt using TinyLlama chat template."""
    return (
        SYS_TAG + "\\n" + SYSTEM_PROMPT + EOS_TAG + "\\n"
        + USER_TAG + "\\n" + user_message + EOS_TAG + "\\n"
        + ASST_TAG + "\\n"
    )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    logger.info(f"Received chat request: {{request.message[:50]}}...")

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Le modele n est pas encore charge. Veuillez patienter."
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
        logger.info(f"Generated response ({{len(response_text)}} chars)")
        return {{"response": response_text}}

    except Exception as e:
        logger.exception("Error during chat generation")
        raise HTTPException(status_code=500, detail=f"Erreur de generation: {{str(e)}}")


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
                logger.error(f"Error processing signature: {{e}}")
                pdf.cell(200, 10, txt="[Signature Error]", ln=1)

        # Output PDF to temporary file
        filename = f"prescription_{{uuid.uuid4()}}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)

        logger.info(f"Successfully generated PDF: {{filename}}")
        return FileResponse(filepath, filename=filename, media_type="application/pdf")

    except Exception as e:
        logger.exception("Error during PDF generation")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {{str(e)}}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
'''

with open("/Users/pierre/Projets/Vocalis/backend/main.py", "w") as f:
    f.write(content)

print("main.py generated successfully")
