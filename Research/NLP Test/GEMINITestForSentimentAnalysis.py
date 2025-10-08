from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

client = genai.Client(api_key = GEMINI_API_KEY)

prompt = """You are a sentiment analyzer. Classify the following sentence into a number from 1-9 representing the positiveness where 5 equals neutal and 9 equals extremely positive.

please only return the number.

Sentence: "I feel tired"
Sentiment:
"""

response = client.models.generate_content(
    model = "gemini-2.5-flash", contents = prompt
)
print(response.text)