#!/bin/bash
# TradeWise Complete Startup Script (Mac/Linux/Git Bash)
# Starts both backend and frontend servers automatically

echo "=========================================="
echo "Starting TradeWise Application"
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

echo "[1/2] Starting Backend Server (Flask)..."

# Start backend in background
cd server
python server.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "Backend started (PID: $BACKEND_PID)"
echo "Backend logs: backend.log"

# Wait for backend to initialize
sleep 3

echo ""
echo "[2/2] Starting Frontend Server (React)..."
echo ""

# Start frontend in background
cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "Frontend started (PID: $FRONTEND_PID)"
echo "Frontend logs: frontend.log"

echo ""
echo "=========================================="
echo "TradeWise is running!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:5001 (PID: $BACKEND_PID)"
echo "Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "To stop the servers, run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or create a stop script with:"
echo "  echo $BACKEND_PID > .backend.pid"
echo "  echo $FRONTEND_PID > .frontend.pid"
echo ""

# Save PIDs for easy stopping
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo "PIDs saved to .backend.pid and .frontend.pid"
echo ""
echo "Browser should open automatically in a few seconds..."
echo "Press Ctrl+C to keep servers running in background"
echo ""

# Keep script running to show it's active
wait
