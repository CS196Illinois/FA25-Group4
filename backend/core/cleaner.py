import json
import re
import logging
from typing import Dict, Optional, List
import yfinance as yf
import requests
from utils.config import GEMINI, POLYGON_KEY, gemini_generate_with_fallback

logger = logging.getLogger(__name__)


def validate_ticker_yfinance(ticker: str, expected_company: str) -> Optional[Dict[str, str]]:
    """
    Validate ticker using yfinance and return official company info.

    Args:
        ticker: Stock ticker symbol to validate
        expected_company: Expected company name from LLM

    Returns:
        Dict with 'company' and 'ticker' if valid, None if invalid/error
    """
    if not ticker:
        return None

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Check if ticker exists and has basic info
        if not info or 'symbol' not in info:
            logger.warning(f"Ticker '{ticker}' not found in yfinance")
            return None

        # Get official company name
        official_name = info.get('longName') or info.get('shortName') or expected_company

        # Basic sanity check: if yfinance returns a name, compare with expected
        if official_name and expected_company:
            # Fuzzy match: check if key words overlap
            expected_words = set(expected_company.lower().split())
            official_words = set(official_name.lower().split())

            # Remove common words
            stop_words = {'inc', 'corp', 'ltd', 'llc', 'corporation', 'company', 'co', 'the'}
            expected_words -= stop_words
            official_words -= stop_words

            # Check for overlap
            if expected_words and official_words:
                overlap = expected_words & official_words
                if not overlap:
                    logger.warning(f"Company name mismatch: expected '{expected_company}', got '{official_name}'")
                    # Still return it but log the mismatch

        logger.info(f"Validated ticker '{ticker}' -> '{official_name}'")
        return {"company": official_name, "ticker": ticker.upper()}

    except Exception as e:
        logger.warning(f"yfinance validation error for '{ticker}': {e}")
        return None


def validate_ticker_polygon(ticker: str) -> Optional[Dict[str, str]]:
    """
    Validate ticker using Polygon.io API (fallback validation).

    Args:
        ticker: Stock ticker symbol to validate

    Returns:
        Dict with 'company' and 'ticker' if valid, None if invalid/error
    """
    if not ticker or not POLYGON_KEY:
        return None

    try:
        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}"
        params = {"apiKey": POLYGON_KEY}

        resp = requests.get(url, params=params, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', {})

            if results:
                company_name = results.get('name', ticker)
                logger.info(f"Polygon validated ticker '{ticker}' -> '{company_name}'")
                return {"company": company_name, "ticker": ticker.upper()}

        logger.warning(f"Polygon could not validate ticker '{ticker}' (status {resp.status_code})")
        return None

    except Exception as e:
        logger.warning(f"Polygon validation error for '{ticker}': {e}")
        return None


def clean_company_and_ticker(user_company: str) -> Dict:
    """
    Resolve user company input to normalized name and ticker symbol.

    Uses Gemini Pro AI + external validation to:
    1. Clean and normalize company name
    2. Resolve to primary U.S. stock ticker
    3. Validate ticker against yfinance/Polygon
    4. Return candidates for user confirmation if uncertain

    Args:
        user_company: Raw user input (company name, ticker, or nickname)

    Returns:
        Dict with keys:
        - 'company': Normalized company name
        - 'ticker': Validated ticker symbol (may be empty)
        - 'candidates': List of candidate matches (if needs_confirmation=True)
        - 'needs_confirmation': Bool indicating if user input is needed
        - 'confidence': LLM confidence score (0-100)
    """
    prompt = (
        "You are a finance ticker resolver.\n"
        "Given a user input that might refer to a public company, ETF, fund, commodity future, or brand nickname:\n"
        "1. Infer the most likely official entity name.\n"
        "2. Infer the most likely primary U.S.-tradable market symbol for that thing "
        "(stock ticker, ETF ticker, mutual fund ticker, or widely quoted futures symbol like GC=F for gold futures).\n"
        "3. Estimate confidence from 0-100.\n"
        "4. If multiple possibilities exist, you may provide alternatives.\n\n"
        "Return ONLY strict JSON:\n"
        '{\n'
        '  "company": "<clean name>",\n'
        '  "ticker": "<symbol or empty string if totally unknown>",\n'
        '  "confidence": <integer 0-100>,\n'
        '  "alternatives": [{"company": "<name>", "ticker": "<symbol>"}]  // optional\n'
        '}\n'
        "Do not add any commentary.\n\n"
        f'User text: "{user_company}"\n'
        "JSON:"
    )

    original = user_company.strip()

    try:
        logger.info(f"Resolving company: {original}")
        resp = gemini_generate_with_fallback(prompt)
        raw = (getattr(resp, "text", "") or "").strip()

        # Attempt to extract the first {...} block
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            logger.warning(f"Gemini did not return JSON for '{original}'. Using original value.")
            return {
                "company": original,
                "ticker": "",
                "candidates": None,
                "needs_confirmation": False,
                "confidence": 0
            }

        data = json.loads(m.group(0))

        company = (data.get("company") or original).strip()
        ticker = (data.get("ticker") or "").strip().upper()
        confidence = data.get("confidence", 0)
        alternatives = data.get("alternatives", [])

        logger.info(f"Resolved '{original}' -> company='{company}', ticker='{ticker}', confidence={confidence}")

        # High confidence (>=80): Validate and return if valid
        if confidence >= 80 and ticker:
            validated = validate_ticker_yfinance(ticker, company)
            if validated:
                logger.info(f"High confidence + validated: using '{ticker}'")
                return {
                    "company": validated["company"],
                    "ticker": validated["ticker"],
                    "candidates": None,
                    "needs_confirmation": False,
                    "confidence": confidence
                }
            else:
                # Validation failed - try Polygon fallback
                validated = validate_ticker_polygon(ticker)
                if validated:
                    logger.info(f"High confidence + Polygon validated: using '{ticker}'")
                    return {
                        "company": validated["company"],
                        "ticker": validated["ticker"],
                        "candidates": None,
                        "needs_confirmation": False,
                        "confidence": confidence
                    }
                # Validation failed - fall through to ask user
                logger.warning(f"High confidence but validation failed for '{ticker}'")

        # Medium confidence (50-79) or validation failed: prepare candidates for user
        if confidence >= 50 or (confidence >= 80 and ticker):
            candidates = []

            # Add primary candidate if ticker exists
            if ticker:
                validated = validate_ticker_yfinance(ticker, company)
                if validated:
                    candidates.append({
                        "company": validated["company"],
                        "ticker": validated["ticker"],
                        "confidence": confidence
                    })
                else:
                    # Add unvalidated candidate with warning
                    candidates.append({
                        "company": company,
                        "ticker": ticker,
                        "confidence": confidence,
                        "validated": False
                    })

            # Add alternatives if provided
            for alt in alternatives:
                alt_ticker = alt.get("ticker", "").strip().upper()
                alt_company = alt.get("company", "").strip()
                if alt_ticker:
                    validated = validate_ticker_yfinance(alt_ticker, alt_company)
                    if validated:
                        candidates.append({
                            "company": validated["company"],
                            "ticker": validated["ticker"],
                            "confidence": alt.get("confidence", confidence - 10)
                        })

            if candidates:
                logger.info(f"Medium confidence: returning {len(candidates)} candidates for user confirmation")
                return {
                    "company": company,
                    "ticker": "",
                    "candidates": candidates,
                    "needs_confirmation": True,
                    "confidence": confidence
                }

        # Low confidence (<50) or no ticker: fail closed
        logger.warning(f"Low confidence ({confidence}) for '{original}' - returning empty ticker")
        return {
            "company": original,
            "ticker": "",
            "candidates": None,
            "needs_confirmation": True,
            "confidence": confidence
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for '{original}': {e}")
        return {
            "company": original,
            "ticker": "",
            "candidates": None,
            "needs_confirmation": False,
            "confidence": 0
        }

    except Exception as e:
        # Fail-closed: on any error, return original input with no ticker
        logger.error(f"Error resolving company '{original}': {e}", exc_info=True)
        return {
            "company": original,
            "ticker": "",
            "candidates": None,
            "needs_confirmation": False,
            "confidence": 0
        }
