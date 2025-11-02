import json
import re
import logging
from typing import Dict
from config import GEMINI

logger = logging.getLogger(__name__)

def clean_company_and_ticker(user_company: str) -> Dict[str, str]:
    """
    Resolve user company input to normalized name and ticker symbol.

    Uses Gemini AI to:
    1. Clean and normalize company name
    2. Resolve to primary U.S. stock ticker

    Args:
        user_company: Raw user input (company name, ticker, or nickname)

    Returns:
        Dict with 'company' and 'ticker' keys (ticker may be empty string)
    """
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
        logger.info(f"Resolving company: {original}")
        resp = GEMINI.generate_content(prompt)
        raw = (getattr(resp, "text", "") or "").strip()

        # Attempt to extract the first {...} block
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            logger.warning(f"Gemini did not return JSON for '{original}'. Using original value.")
            return {"company": original, "ticker": ""}

        data = json.loads(m.group(0))

        company = (data.get("company") or original).strip()
        ticker = (data.get("ticker") or "").strip().upper()
        confidence = data.get("confidence", 0)

        logger.info(f"Resolved '{original}' -> company='{company}', ticker='{ticker}', confidence={confidence}")
        return {"company": company, "ticker": ticker}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for '{original}': {e}")
        return {"company": original, "ticker": ""}

    except Exception as e:
        # Fail-closed: on any error, return original input with no ticker
        logger.error(f"Error resolving company '{original}': {e}", exc_info=True)
        return {"company": original, "ticker": ""}
