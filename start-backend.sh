#!/bin/bash

# Vocalis - Start Backend Only

echo "Starting Vocalis Backend..."
echo ""

cd backend

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -q -r requirements.txt

# Start server
echo "[3/3] Starting server..."
echo ""
python main.py
