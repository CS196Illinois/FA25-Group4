# Running TradeWise Locally

## Quick Start (One Command!)

**Windows:**
```bash
start-tradewise.bat
```

**Mac/Linux/Git Bash:**
```bash
./start-tradewise.sh
```

This automatically starts both backend and frontend servers!

## Stopping the Servers

**Windows:**
```bash
stop-tradewise.bat
```

**Mac/Linux/Git Bash:**
```bash
./stop-tradewise.sh
```

Or press Ctrl+C in the terminal windows.

---

## Alternative: Manual Startup

If you prefer to run servers separately:

### Option 1: Using Individual Scripts

**Windows (Command Prompt/PowerShell):**
```bash
# Terminal 1 - Start Backend
start-backend.bat

# Terminal 2 - Start Frontend (in a new terminal)
start-frontend.bat
```

**Mac/Linux/Git Bash:**
```bash
# Terminal 1 - Start Backend
./start-backend.sh

# Terminal 2 - Start Frontend (in a new terminal)
./start-frontend.sh
```

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd server
python server.py
# Server runs on http://localhost:5001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
# Opens automatically at http://localhost:3000
```

## Accessing the Application

Once both servers are running:
1. Frontend will automatically open at **http://localhost:3000**
2. Backend API runs at **http://localhost:5001**
3. Use the **Chat** tab to analyze companies

## Requirements

### Environment Variables
Make sure your `.env` file exists in the root directory with:
```
GEMINI_KEY=your_actual_api_key_here  # REQUIRED
POLYGON_KEY=optional
FINNHUB_KEY=optional
NEWS_KEY=optional
```

See [.env.example](.env.example) for details on getting API keys.

### Dependencies
- **Python 3.8+** with packages from `requirements.txt`
- **Node.js 14+** with packages from `frontend/package.json`

## Testing the Setup

1. Navigate to http://localhost:3000
2. Click the **Chat** tab
3. Enter a company name (e.g., "Apple" or "Microsoft")
4. Select "Light" or "Detailed" mode
5. Click the search icon 🔍
6. Wait 30-60 seconds for comprehensive analysis

## Troubleshooting

**Backend won't start:**
- Check that `.env` file exists and has GEMINI_KEY
- Run `pip install -r requirements.txt`
- Check port 5001 isn't already in use

**Frontend won't start:**
- Run `cd frontend && npm install`
- Check port 3000 isn't already in use
- Clear npm cache: `npm cache clean --force`

**Analysis fails:**
- Verify GEMINI_KEY is valid
- Check backend terminal for error messages
- Ensure internet connection is active
- **Note:** The app uses `gemini-3-pro-preview` by default with automatic fallback to `gemini-2.5-pro` if the primary model fails or hits rate limits

**CORS errors:**
- Make sure backend is running on port 5001
- Frontend expects backend at http://localhost:5001

## Stopping the Servers

Press **Ctrl+C** in each terminal window to stop the servers.
