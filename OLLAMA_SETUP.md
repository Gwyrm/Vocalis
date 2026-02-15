# Ollama Setup Guide for Vocalis

## Overview

Vocalis now uses **Mistral 7B** via **Ollama** for medical data extraction instead of the local TinyLlama model.

This provides:
- ✅ Much better extraction accuracy (all 7 prescription fields extracted correctly)
- ✅ Proper French language support
- ✅ Reliable JSON/structured output parsing
- ✅ Local inference (no cloud API calls needed)

## Installation

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

### 2. Download Mistral 7B Model

```bash
ollama pull mistral
# Downloads ~4.4 GB model
# Takes 5-10 minutes depending on internet speed
```

Verify it's installed:
```bash
ollama list
# Should show: mistral:latest    6577803aa9a0    4.4 GB
```

## Running Vocalis with Ollama

### Terminal 1: Start Ollama Server

```bash
ollama serve
# Ollama server starts on http://localhost:11434
```

### Terminal 2: Start Backend

```bash
cd backend
python main.py
# Backend starts on http://localhost:8080
```

### Terminal 3: Start Frontend (optional)

```bash
cd frontend
flutter run -d chrome
```

## Verification

### Check Ollama is running

```bash
curl http://localhost:11434/api/tags
# Should return list of available models
```

### Check Backend can see Ollama

```bash
curl http://localhost:8080/api/health
```

Expected response:
```json
{
  "status": "ok",
  "backend": "running",
  "ollama_available": true,
  "ollama_url": "http://localhost:11434",
  "model": "mistral"
}
```

## Usage

The extraction works automatically. When you type a prescription message:

```
Patient Jean Dupont, 45 ans, hypertension,
Lisinopril 10mg une fois par jour, 3 mois, à jeun
```

Mistral will extract:
- patientName: Jean Dupont
- patientAge: 45 ans
- diagnosis: Hypertension
- medication: Lisinopril
- dosage: 10mg once per day
- duration: 3 mois
- specialInstructions: Taking at fasting state

## Configuration

### Using a Different Model

Set environment variables before running:

```bash
# Use a different Ollama model
export OLLAMA_MODEL=neural-chat
python main.py

# Or use a remote Ollama server
export OLLAMA_BASE_URL=http://192.168.1.100:11434
python main.py
```

### Available Models

Popular models for this use case:

```bash
ollama pull mistral           # 7B, good general purpose
ollama pull neural-chat       # 7B, good chat/instruction following
ollama pull openhermes        # 7B, instruction tuned
ollama pull llama2            # 7B/13B/70B options
ollama pull dolphin-mixtral   # High quality, larger model
```

## Troubleshooting

### "Ollama not available" error

**Problem**: Backend says Ollama is unavailable

**Solutions**:
```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Check if it's on a different port
curl http://localhost:11434/api/tags

# 3. If on a different host, set the URL
export OLLAMA_BASE_URL=http://your-ollama-host:11434
python main.py
```

### Slow extraction (takes >10 seconds)

**Possible causes**:
- First inference with model (loads into memory, ~20-30s normal)
- CPU-only inference (no GPU acceleration)
- Model is too large for your hardware

**Solutions**:
- Use a smaller model: `ollama pull mistral:7b` instead of larger models
- Enable GPU: Check Ollama GPU setup at https://ollama.ai
- Increase max_tokens timeout in backend if needed

### Out of memory errors

**Problem**: Ollama crashes with out of memory error

**Solutions**:
- Use a smaller model (3B instead of 7B)
- Close other applications
- Allocate more RAM to Ollama

```bash
# Ollama automatically uses available memory
# But you can limit it if needed
export OLLAMA_MAX_MEMORY=8000000000  # 8GB
ollama serve
```

## Performance

### Extraction Times (Mistral 7B)

- First run (model loading): ~20-30 seconds
- Subsequent runs: ~2-5 seconds per extraction
- Total chat response: ~3-8 seconds

### System Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 10 GB free

**Recommended**:
- CPU: 8+ cores
- RAM: 16 GB
- GPU: NVIDIA with 8GB+ VRAM (optional, for speed)

## Architecture

```
┌─────────────────────────────────────┐
│     Vocalis Backend (FastAPI)       │
│     Port 8080                       │
│   ┌──────────────────────────────┐ │
│   │  Chat Endpoint               │ │
│   │  - Receives user message     │ │
│   │  - Calls Ollama API          │ │
│   │  - Extracts medical data     │ │
│   │  - Stores in SQLite DB       │ │
│   └──────────────────────────────┘ │
└────────────┬────────────────────────┘
             │
             │ HTTP requests
             ↓
┌─────────────────────────────────────┐
│    Ollama Server                    │
│    Port 11434                       │
│   ┌──────────────────────────────┐ │
│   │  Mistral 7B Model            │ │
│   │  - Inference                 │ │
│   │  - Text extraction           │ │
│   │  - JSON parsing              │ │
│   └──────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Switching Back to TinyLlama (Local)

If you want to use the old local TinyLlama model without Ollama:

```bash
cd backend
git checkout HEAD~1 main.py  # Revert to previous version
pip install llama-cpp-python  # Install local LLM support
python main.py
```

However, **Mistral 7B via Ollama is recommended** for better accuracy.

## Next Steps

- Test the complete prescription workflow
- Adjust prompts if needed for specific medical scenarios
- Consider GPU acceleration for faster inference
- Deploy to production with appropriate resource allocation

## References

- Ollama Documentation: https://ollama.ai
- Mistral Model Card: https://huggingface.co/mistralai/Mistral-7B
- Vocalis QUICKSTART: See QUICKSTART.md
