#!/bin/bash

# Vocalis - Check Prerequisites

echo ""
echo "=========================================="
echo "  Vocalis - Checking Prerequisites"
echo "=========================================="
echo ""

ERRORS=0

# Check Python
echo -n "Python 3......... "
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "OK ($VERSION)"
else
    echo "MISSING"
    echo "  Install from: https://www.python.org"
    ERRORS=$((ERRORS + 1))
fi

# Check Flutter
echo -n "Flutter......... "
if command -v flutter &> /dev/null; then
    echo "OK"
else
    echo "MISSING"
    echo "  Install from: https://flutter.dev"
    ERRORS=$((ERRORS + 1))
fi

# Check Dart
echo -n "Dart............ "
if command -v dart &> /dev/null; then
    echo "OK"
else
    echo "MISSING (comes with Flutter)"
    ERRORS=$((ERRORS + 1))
fi

# Check model
echo -n "TinyLlama model. "
if [ -f "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" ]; then
    SIZE=$(du -h "backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" 2>/dev/null | cut -f1)
    echo "OK ($SIZE)"
else
    echo "MISSING"
    echo ""
    echo "Download TinyLlama from:"
    echo "  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    echo ""
    echo "Or use Ollama (recommended):"
    echo "  1. Install Ollama from https://ollama.ai"
    echo "  2. Run: ollama pull tinyllama"
    echo ""
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✓ All prerequisites OK!"
    echo ""
    echo "Ready to start:"
    echo "  ./start-all.sh       (Backend + Frontend)"
    echo "  ./start-backend.sh   (Backend only)"
    echo "  ./start-frontend.sh  (Frontend only)"
else
    echo "✗ Please install missing prerequisites above"
    exit 1
fi

echo ""
