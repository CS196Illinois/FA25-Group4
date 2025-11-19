import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_KEY  = os.getenv("GEMINI_KEY")
POLYGON_KEY = os.getenv("POLYGON_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
NEWS_KEY    = os.getenv("NEWS_KEY")

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_KEY missing. Add it to .env")

genai.configure(api_key=GEMINI_KEY)

# Use Pro model with low temperature for better accuracy on lesser-known companies
GEMINI = genai.GenerativeModel(
    "gemini-3-pro-preview",
    generation_config={
        "temperature": 0.1,  # More deterministic, less hallucination
        "top_p": 0.8,
        "response_mime_type": "application/json"
    }
)

FINANCE_DOMAINS = [
    "reuters.com","bloomberg.com","ft.com","wsj.com","cnbc.com",
    "marketwatch.com","finance.yahoo.com","seekingalpha.com","investopedia.com",
    "forbes.com","themotleyfool.com","barrons.com","benzinga.com"
]