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

class ChatRequest(BaseModel):
    message: str
    model: str = "mistral" # Default model, can be changed

class PrescriptionRequest(BaseModel):
    content: str
    signature_base64: str # Base64 encoded image string

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        async with httpx.AsyncClient() as client:
            # Assuming Ollama is running locally on default port
            ollama_url = "http://127.0.0.1:11434/api/generate"
            payload = {
                "model": request.model,
                "prompt": request.message,
                "stream": False
            }
            response = await client.post(ollama_url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return {"response": data.get("response", "")}
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/generate-pdf")
async def generate_pdf(request: PrescriptionRequest):
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
                print(f"Error processing signature: {e}")
                pdf.cell(200, 10, txt="[Signature Error]", ln=1)

        # Output PDF to temporary file
        filename = f"prescription_{uuid.uuid4()}.pdf"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        pdf.output(filepath)
        
        return FileResponse(filepath, filename=filename, media_type='application/pdf')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
