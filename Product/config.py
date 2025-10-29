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
GEMINI = genai.GenerativeModel("gemini-2.5-flash")

FINANCE_DOMAINS = [
    "reuters.com","bloomberg.com","ft.com","wsj.com","cnbc.com",
    "marketwatch.com","finance.yahoo.com","seekingalpha.com","investopedia.com",
    "forbes.com","themotleyfool.com","barrons.com","benzinga.com"
]