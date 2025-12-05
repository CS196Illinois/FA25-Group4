#!/bin/bash
# TradeWise Backend Startup Script

echo "=========================================="
echo "Starting TradeWise Backend Server"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and add your API keys"
    exit 1
fi

# Check if GEMINI_KEY is set
if ! grep -q "GEMINI_KEY=.*[^your_gemini_api_key_here]" .env 2>/dev/null; then
    echo "WARNING: GEMINI_KEY might not be configured in .env"
    echo "The app requires a valid GEMINI_KEY to function"
    echo ""
fi

echo "Starting Flask server on http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

cd server
python server.py
