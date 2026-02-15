#!/bin/bash

# Configuration script for Ollama optimization
# Use this before starting the Vocalis project

echo "Setting up Ollama environment variables for stability..."

# 1. Keep the model in memory indefinitely (avoid cold start crashes/delays)
export OLLAMA_KEEP_ALIVE="-1"

# 2. Prevent loading multiple models at once (save RAM)
export OLLAMA_MAX_LOADED="1"

# 3. Process requests one by one (avoid CPU/GPU saturation)
export OLLAMA_NUM_PARALLEL="1"

# 4. Optional: Enable Flash Attention for NVIDIA GPUs (if applicable)
# export OLLAMA_FLASH_ATTENTION="1"

echo "Environment ready."
echo "You can now start Ollama if it's not already running:"
echo "  ollama serve"
echo ""
echo "And your backend with:"
echo "  export OLLAMA_TIMEOUT=120.0"
echo "  python main.py"
