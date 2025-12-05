# --- Imports ---
import json
import re
import yfinance as yf
import requests   # ✅ add this here
from Product.config import GEMINI   

# --- Helper function ---
def _search_symbol(query: str):
    """Use Yahoo Finance autocomplete API to resolve company names to tickers."""
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if "quotes" in data and len(data["quotes"]) > 0:
            symbol = data["quotes"][0]["symbol"]
            name = data["quotes"][0].get("longname") or data["quotes"][0].get("shortname") or query
            return {"company": name, "ticker": symbol}
    except Exception:
        pass
    return {"company": query, "ticker": ""}

# --- Main function ---
def clean_company_and_ticker(user_company: str):
    original = user_company.strip()

    # Case 1: Input looks like a ticker
    if original.isupper() and 1 <= len(original) <= 5:
        try:
            ticker_obj = yf.Ticker(original)
            info = ticker_obj.info
            if info and "longName" in info:
                return {"company": info["longName"], "ticker": original}
        except Exception:
            pass

    # Case 2: Try Gemini
    try:
        prompt = (
            "You are a finance ticker resolver.\n"
            "Given a user input that might refer to a public company, ETF, fund, commodity future, or brand nickname:\n"
            "1. Infer the most likely official entity name.\n"
            "2. Infer the most likely primary U.S.-tradable market symbol (ticker).\n"
            "Always return the ticker symbol (like TSLA, AAPL, MSFT), never the company name.\n"
            "Return ONLY strict JSON:\n"
            '{ "company": "<clean name>", "ticker": "<symbol>" }\n'
            f'User text: "{user_company}"\nJSON:'
        )
    resp = GEMINI.generate_content(prompt)
    raw = (getattr(resp, "text", "") or "").strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        data = json.loads(m.group(0))
        company = (data.get("company") or original).strip()
        ticker  = (data.get("ticker") or "").strip().upper()

        if ticker:
            try:
                info = yf.Ticker(ticker).info
                if info and "longName" in info:
                    company = info["longName"]
                    return {"company": company, "ticker": ticker}
            except Exception:
                pass

    # Add your fallback here
        if company and not ticker:
            return _search_symbol(company)


    # Case 3: Fallback search via Yahoo Finance autocomplete
    return _search_symbol(original)
