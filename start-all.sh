#!/bin/bash

# Vocalis - Start Backend + Frontend

echo ""
echo "=========================================="
echo "  Vocalis - Starting Backend + Frontend"
echo "=========================================="
echo ""

# Check prerequisites
echo "[SETUP] Checking prerequisites..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Install from: https://www.python.org"
    exit 1
fi
echo "✓ Python 3 found"

# Check Flutter
if ! command -v flutter &> /dev/null; then
    echo "ERROR: Flutter not found"
    echo "Install from: https://flutter.dev"
    exit 1
fi
echo "✓ Flutter found"

# Check model
if [ ! -f "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    echo ""
    echo "WARNING: TinyLlama model not found at:"
    echo "  backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo ""
    echo "Download from:"
    echo "  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    echo ""
    echo "Or use Ollama:"
    echo "  ollama pull tinyllama"
    echo ""
fi

echo ""
echo "=========================================="
echo "  Starting Backend..."
echo "=========================================="
echo ""

# Start backend
cd backend

if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

echo "[3/3] Starting server (background)..."
echo ""
python main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check backend health
if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "✓ Backend started (PID: $BACKEND_PID)"
    echo "  Available at: http://localhost:8080"
else
    echo "✗ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "=========================================="
echo "  Starting Frontend..."
echo "=========================================="
echo ""

cd ../frontend

echo "[1/2] Getting Flutter dependencies..."
flutter pub get -q

echo "[2/2] Running application..."
echo ""
echo "CTRL+C to stop both backend and frontend"
echo ""

# Start frontend
flutter run -d chrome

# Cleanup
echo ""
echo "Stopping backend..."
kill $BACKEND_PID 2>/dev/null || true
