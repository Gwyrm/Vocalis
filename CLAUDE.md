# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Vocalis** is a medical AI assistant application designed to help physicians draft medical prescriptions. It consists of a Flutter cross-platform frontend and a FastAPI Python backend with an embedded TinyLlama LLM.

## Architecture

### Tech Stack
- **Frontend**: Flutter (Dart) - supports web, iOS, Android, macOS, Linux, Windows
- **Backend**: FastAPI (Python) with llama-cpp running TinyLlama 1.1B quantized model
- **API Communication**: REST HTTP (JSON)
- **PDF Generation**: FPDF library with signature support

### Directory Structure
- `/frontend` - Flutter application (Dart)
- `/backend` - FastAPI server (Python)
  - `main.py` - FastAPI application with endpoints for chat and PDF generation
  - `models/` - LLM model storage (TinyLlama GGUF format)
  - `requirements.txt` - Python dependencies
  - `venv/` - Python virtual environment

### Key Architecture Decisions

1. **Embedded LLM**: The backend loads a quantized TinyLlama model (1.1B parameters) at startup via llama-cpp-python. The model is kept in memory across requests for fast inference.

2. **CORS Configuration**: CORS is enabled on the backend for all origins (`allow_origins=["*"]`), with `allow_credentials=False`.

3. **API Base URL Configuration** (Frontend):
   - In production web builds, use `--dart-define=API_URL=http://<server-ip>:8080`
   - In local development, defaults to `http://127.0.0.1:8080`
   - Example: `flutter build web --dart-define=API_URL=http://192.168.1.100:8080`

4. **Model Loading**: The backend uses a lifespan context manager to load the model at startup and release resources at shutdown. If the model fails to load, the entire backend fails gracefully.

## Development Setup

### Backend

**Prerequisites**: Python 3.11+

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Download the TinyLlama model (if not present)
# The model is expected at: backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
# See ollama_setup.sh for Ollama-based model setup

# Run the server (with auto-reload)
python main.py

# Server runs on http://localhost:8080
```

**Environment Variables**:
- `MODEL_PATH` - Path to GGUF model file (default: `backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`)
- `OLLAMA_TIMEOUT` - Timeout for model responses (default: 120.0 seconds)

### Frontend

**Prerequisites**: Flutter SDK 3.11+, Dart 3.11+

```bash
# Navigate to frontend directory
cd frontend

# Get dependencies
flutter pub get

# Run on local device/emulator (defaults to port 8080 localhost)
flutter run

# Run web version (requires API_URL configuration)
flutter run -d chrome

# Build web for production
flutter build web --dart-define=API_URL=http://<server-ip>:8080

# Build for other platforms
flutter build ios
flutter build android
flutter build windows
flutter build linux
flutter build macos
```

## API Endpoints

### `/` (GET)
Returns server status.

### `/api/health` (GET)
Health check endpoint. Returns model load status and model path.
```json
{
  "status": "ok",
  "backend": "running",
  "model_loaded": true,
  "model_path": "/path/to/model.gguf"
}
```

### `/api/chat` (POST)
Chat endpoint for AI-powered medical prescription assistance.

**Request**:
```json
{
  "message": "User input"
}
```

**Response**:
```json
{
  "response": "AI-generated prescription text"
}
```

**Status Codes**:
- `200` - Success
- `503` - Model not loaded
- `500` - Generation error

### `/api/generate-pdf` (POST)
Generate a PDF prescription with signature.

**Request**:
```json
{
  "content": "Prescription text",
  "signature_base64": "data:image/png;base64,..." or "base64_string"
}
```

**Response**: PDF file (binary)

## Common Development Tasks

### Run backend with logging
```bash
cd backend && source venv/bin/activate && python main.py
```

### Run frontend in web mode pointing to local backend
```bash
cd frontend && flutter run -d chrome
```

### Run frontend web build for deployment
```bash
cd frontend && flutter build web --dart-define=API_URL=http://192.168.1.100:8080 --release
```

### Debug model loading issues
Check backend logs for model loading errors. The backend will fail to start if the model file is missing or corrupted. Ensure `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` exists at `backend/models/`.

### Verify API connectivity
```bash
# Check backend health
curl http://localhost:8080/api/health

# Test chat endpoint
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour"}'
```

## Model Deployment

The TinyLlama 1.1B quantized model must be present before the backend starts. The model is referenced at `backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`. For Ollama-based setup, see `ollama_setup.sh`.

## Notes on Language

The system prompt and error messages are in French, as the application targets French-speaking medical professionals. Chat responses are formatted for French medical prescriptions.
