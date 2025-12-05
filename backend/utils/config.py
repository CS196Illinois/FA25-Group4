import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_KEY  = os.getenv("GEMINI_KEY")
POLYGON_KEY = os.getenv("POLYGON_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
NEWS_KEY    = os.getenv("NEWS_KEY")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_KEY missing. Add it to .env")

genai.configure(api_key=GEMINI_KEY)

# Primary model configuration
GEMINI_CONFIG = {
    "temperature": 0.1,  # More deterministic, less hallucination
    "top_p": 0.8,
    "response_mime_type": "application/json"
}

# Use Pro model with low temperature for better accuracy on lesser-known companies
GEMINI = genai.GenerativeModel(
    "gemini-3-pro-preview",
    generation_config=GEMINI_CONFIG
)

# Fallback model - more stable, widely available model
# Using gemini-2.5-pro for better quality and reliability
GEMINI_FALLBACK = genai.GenerativeModel(
    "gemini-2.5-pro",
    generation_config=GEMINI_CONFIG
)


def gemini_generate_with_fallback(prompt: str, use_fallback: bool = True):
    """
    Generate content with automatic fallback to stable model if primary fails.

    Args:
        prompt: The prompt to send to the model
        use_fallback: Whether to use fallback model on primary failure (default True)

    Returns:
        Response object from Gemini

    Raises:
        Exception: If both primary and fallback models fail
    """
    try:
        logger.debug("Attempting generation with primary model (gemini-3-pro-preview)")
        return GEMINI.generate_content(prompt)
    except Exception as e:
        logger.warning(f"Primary model failed: {e}")

        if use_fallback:
            try:
                logger.info("Falling back to gemini-2.5-pro")
                return GEMINI_FALLBACK.generate_content(prompt)
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise Exception(f"Both primary and fallback models failed. Primary: {e}, Fallback: {fallback_error}")
        else:
            # If fallback disabled, re-raise original error
            raise

FINANCE_DOMAINS = [
    "reuters.com","bloomberg.com","ft.com","wsj.com","cnbc.com",
    "marketwatch.com","finance.yahoo.com","seekingalpha.com","investopedia.com",
    "forbes.com","themotleyfool.com","barrons.com","benzinga.com"
]