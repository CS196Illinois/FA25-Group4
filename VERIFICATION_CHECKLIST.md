# Integration Verification Checklist

## ✅ Pre-Flight Check

Before running the server, verify:

- [ ] Python installed: `python --version` (should be 3.7+)
- [ ] Flask installed: `pip install flask flask-cors`
- [ ] Git repo: You're in `FA25-Group4` directory
- [ ] File exists: `front-end/control/server.py`

---

## ✅ Server Startup Verification

Run: `cd front-end/control && python server.py`

Check for:
- [ ] No import errors
- [ ] No syntax errors
- [ ] Output shows: "Starting TradeWise Integrated Backend Server"
- [ ] Output shows: "Server running on: http://localhost:5000"
- [ ] No "Address already in use" error

---

## ✅ API Endpoint Verification

Test each endpoint (in PowerShell):

```bash
# Health Check
curl http://localhost:5000/api/health
# ✓ Should return: {"status":"ok",...}
```

```bash
# Save Preferences
curl -X POST http://localhost:5000/api/preferences `
  -H "Content-Type: application/json" `
  -d '{
    "user_id":"test",
    "riskTolerance":"medium",
    "totalInvestment":50000,
    "targetedReturns":8.5,
    "areasInterested":["Tech"]
  }'
# ✓ Should return: {"status":"success",...}
```

```bash
# Get Preferences
curl http://localhost:5000/api/preferences/test
# ✓ Should return: {"status":"success","data":{...}}
```

```bash
# Save Query
curl -X POST http://localhost:5000/api/analysis/query `
  -H "Content-Type: application/json" `
  -d '{"company_name":"Apple","detail_level":"detailed"}'
# ✓ Should return: {"status":"success",...}
```

```bash
# Get All Queries
curl http://localhost:5000/api/analysis/queries
# ✓ Should return: {"status":"success","queries":[...],"count":...}
```

```bash
# Get Latest Query
curl http://localhost:5000/api/analysis/queries/latest
# ✓ Should return: {"status":"success","query":{...}}
```

---

## ✅ File Creation Verification

After running some requests:

Check that these files exist:
- [ ] `user_preferences/test_preferences.json` (created by save preferences)
- [ ] `analysis_queries/queries.json` (created by save query)

Check file contents:
- [ ] Preferences file contains: `riskTolerance`, `totalInvestment`, `targetedReturns`, `areasInterested`, `timestamp`
- [ ] Queries file contains: array with `company_name`, `detail_level`, `timestamp`

---

## ✅ React Frontend Verification

Run: `cd front-end && npm start`

Check:
- [ ] React opens at http://localhost:3000
- [ ] No console errors
- [ ] Navigation buttons work (Main, Chat, Sign In, Register)
- [ ] Main tab shows preferences panel on right side
- [ ] Chat tab shows input field with toggle switch

---

## ✅ Frontend-Backend Integration Verification

### Test Preferences Panel
1. Go to http://localhost:3000
2. Click "Main" tab
3. Fill preferences form:
   - Select risk: Medium
   - Investment: 50000
   - Returns: 8.5
   - Select areas: Technology, Healthcare
4. Click "Save Preferences"

Check:
- [ ] Message shows: "✓ Preferences saved successfully to backend!"
- [ ] File created: `user_preferences/default_user_preferences.json`
- [ ] Data in file matches what you entered

### Test Chat Interface
1. Go to http://localhost:3000
2. Click "Chat" tab
3. Type company name: "Apple Inc."
4. Toggle to: "Detailed"
5. Press Enter or click 🔍

Check:
- [ ] Chat shows: "Analyze Apple Inc. (detailed mode)"
- [ ] File created: `analysis_queries/queries.json`
- [ ] File contains: "Apple Inc." and "detailed"

---

## ✅ Data Persistence Verification

With server still running:

1. Save different preferences for another user:
```bash
curl -X POST http://localhost:5000/api/preferences `
  -H "Content-Type: application/json" `
  -d '{
    "user_id":"user2",
    "riskTolerance":"high",
    "totalInvestment":100000,
    "targetedReturns":15,
    "areasInterested":["Energy"]
  }'
```

Check:
- [ ] `user_preferences/user2_preferences.json` created
- [ ] Both user files exist independently

2. Submit multiple queries from chat

Check:
- [ ] `analysis_queries/queries.json` has multiple entries
- [ ] All entries have timestamps
- [ ] List growing with each submission

---

## ✅ Error Handling Verification

Test error scenarios:

```bash
# Invalid endpoint
curl http://localhost:5000/api/invalid
# ✓ Should return 404 error
```

```bash
# Missing required field
curl -X POST http://localhost:5000/api/analysis/query `
  -H "Content-Type: application/json" `
  -d '{"detail_level":"detailed"}'
# ✓ Should return error message
```

```bash
# Invalid detail level
curl -X POST http://localhost:5000/api/analysis/query `
  -H "Content-Type: application/json" `
  -d '{"company_name":"Apple","detail_level":"invalid"}'
# ✓ Should return error message
```

---

## ✅ Performance Verification

Check response times are reasonable:

```bash
# Should respond quickly
time curl http://localhost:5000/api/analysis/queries
# ✓ Should complete in <100ms
```

---

## ✅ Server Stability Verification

1. Keep server running for 5 minutes
2. Make several requests
3. Check that:
   - [ ] No memory leaks (CPU/RAM stable)
   - [ ] All requests complete successfully
   - [ ] No error messages in server console
   - [ ] Server doesn't crash

---

## ✅ Documentation Verification

Check that these files exist:
- [ ] `front-end/control/INTEGRATED_SERVER_GUIDE.md`
- [ ] `front-end/control/QUICK_START.md`
- [ ] `INTEGRATION_COMPLETE.md`

---

## 🎉 Final Checklist

If ALL of the above are checked:

✅ **Integration is successful!**

You can now:
1. Run `python front-end/control/server.py` to start backend
2. Run `npm start` in `front-end/` to start frontend
3. Access both preferences and analysis queries
4. Store data persistently in JSON files
5. Build your app with confidence!

---

## 🚀 Next Steps

With integration complete, you can:

1. **Clean up** (optional):
   - Delete old files: `app.py`, `analysis_query_*.py`, `preferences_*.py` from root
   - These are no longer needed

2. **Production ready**:
   - Set `debug=False` in server.py for production
   - Add proper logging instead of print statements
   - Add request validation and authentication

3. **Expand functionality**:
   - Connect sentiment analysis to real models
   - Add user authentication
   - Add database instead of JSON files
   - Add caching layer
   - Add API rate limiting

---

## 📞 Troubleshooting Reference

If something fails at any step, refer to:
- `INTEGRATION_COMPLETE.md` - Full overview
- `front-end/control/INTEGRATED_SERVER_GUIDE.md` - Detailed guide
- `front-end/control/QUICK_START.md` - Quick reference

Most common issue: `pip install flask flask-cors` not run

Happy coding! 🎉
