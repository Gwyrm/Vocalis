from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import httpx
from fpdf import FPDF
import base64
import os
import tempfile
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vocalis-backend")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Vocalis Backend is running"}

@app.get("/api/health")
async def health_check():
    ollama_base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    try:
        async with httpx.AsyncClient() as client:
            # Check if Ollama is responsive
            response = await client.get(f"{ollama_base_url}/api/tags", timeout=5.0)
            ollama_status = "ok" if response.status_code == 200 else "error"
    except Exception:
        ollama_status = "unavailable"
    
    return {
        "status": "ok",
        "backend": "running",
        "ollama": ollama_status,
        "ollama_url": ollama_base_url
    }

class ChatRequest(BaseModel):
    message: str
    model: str = "mistral" # Default model, can be changed

class PrescriptionRequest(BaseModel):
    content: str
    signature_base64: str # Base64 encoded image string

@app.post("/api/chat")
async def chat(request: ChatRequest):
    logger.info(f"Received chat request for model: {request.model}")
    try:
        async with httpx.AsyncClient() as client:
            ollama_base_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
            ollama_url = f"{ollama_base_url}/api/generate"
            ollama_timeout = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))
            
            payload = {
                "model": request.model,
                "prompt": request.message,
                "stream": False
            }
            
            try:
                response = await client.post(ollama_url, json=payload, timeout=ollama_timeout)
                response.raise_for_status()
                data = response.json()
                logger.info("Successfully received response from Ollama")
                return {"response": data.get("response", "")}
            
            except httpx.ConnectError as e:
                logger.error(f"Could not connect to Ollama at {ollama_url}: {e}")
                raise HTTPException(status_code=503, detail="Ollama service is unavailable. Please ensure it is running.")
            
            except httpx.TimeoutException as e:
                logger.error(f"Ollama request timed out after {ollama_timeout}s: {e}")
                raise HTTPException(status_code=504, detail="Ollama took too long to respond. The model might be loading or too heavy.")
            
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama returned an error status {e.response.status_code}: {e.response.text}")
                raise HTTPException(status_code=e.response.status_code, detail=f"Ollama error: {e.response.text}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in chat endpoint")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/generate-pdf")
async def generate_pdf(request: PrescriptionRequest):
    logger.info("Received PDF generation request")
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Ordonnance Médicale", ln=1, align='C')
        pdf.ln(10)
        
        # Add Content
        pdf.set_font("Arial", size=12)
        # multi_cell handles text wrapping
        pdf.multi_cell(0, 10, txt=request.content)
        pdf.ln(20)
        
        # Handle Signature
        if request.signature_base64:
            # Decode base64 image
            try:
                # Remove header if present (e.g., "data:image/png;base64,")
                if "," in request.signature_base64:
                    signature_data = request.signature_base64.split(",")[1]
                else:
                    signature_data = request.signature_base64
                
                img_data = base64.b64decode(signature_data)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                    tmp_img.write(img_data)
                    tmp_img_path = tmp_img.name
                
                pdf.image(tmp_img_path, w=50) # Width 50mm
                os.remove(tmp_img_path) # Clean up temp file
                
            except Exception as e:
                logger.error(f"Error processing signature: {e}")
                pdf.cell(200, 10, txt="[Signature Error]", ln=1)

        # Output PDF to temporary file
        filename = f"prescription_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)
        
        logger.info(f"Successfully generated PDF: {filename}")
        return FileResponse(filepath, filename=filename, media_type='application/pdf')

    except Exception as e:
        logger.exception("Error during PDF generation")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
