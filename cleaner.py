import json, re
from typing import List, Dict, Any
from config import GEMINI

def clean_company_and_ticker(user_company: str):
    prompt = (
        "You are a finance ticker resolver.\n"
        "Given a user input that might refer to a public company, ETF, fund, commodity future, or brand nickname:\n"
        "1. Infer the most likely official entity name.\n"
        "2. Infer the most likely primary U.S.-tradable market symbol for that thing "
        "(stock ticker, ETF ticker, mutual fund ticker, or widely quoted futures symbol like GC=F for gold futures).\n"
        "3. Estimate confidence from 0-100.\n\n"
        "Return ONLY strict JSON:\n"
        '{\n'
        '  "company": "<clean name>",\n'
        '  "ticker": "<symbol or empty string if totally unknown>",\n'
        '  "confidence": <integer 0-100>\n'
        '}\n'
        "Do not add any commentary.\n\n"
        f'User text: "{user_company}"\n'
        "JSON:"
    )


    original = user_company.strip()
    try:
        resp = GEMINI.generate_content(prompt)
        raw = (getattr(resp, "text", "") or "").strip()
        # attempt to extract the first {...} block
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            # model didn't send JSON
            return {"company": original, "ticker": ""}

        data = json.loads(m.group(0))

        company = (data.get("company") or original).strip()
        ticker  = (data.get("ticker") or "").strip().upper()

        return {"company": company, "ticker": ticker}
    except Exception:
        # fail closed
        return {"company": original, "ticker": ""}