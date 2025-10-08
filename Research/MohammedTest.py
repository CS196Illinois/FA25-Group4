from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY")
NEWS_KEY = os.getenv("NEWS_KEY")