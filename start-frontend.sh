#!/bin/bash
# TradeWise Frontend Startup Script

echo "=========================================="
echo "Starting TradeWise Frontend"
echo "=========================================="
echo ""

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "Starting React development server on http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

cd frontend
npm start
