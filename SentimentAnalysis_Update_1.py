# --- Imports ---
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import nltk
from nltk import word_tokenize, pos_tag
from transformers import pipeline
import google.generativeai as genai

# --- NLTK Setup ---
nltk.download('punkt')
nltk.download('all')

# --- Environment Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_KEY")
genai.configure(api_key=api_key)

# --- Gemini Model Setup ---
# Replace with a supported model name from genai.list_models()
GEMINI = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# --- Utility Functions ---
def preprocess(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_aspects_nltk(text):
    tokens = word_tokenize(text, preserve_line=True)
    tagged = pos_tag(tokens)
    nouns = [word.lower() for word, tag in tagged if tag.startswith("NN") and len(word) > 2]
    return list(set(nouns))

def weighted_sentiment(aspect_results, weights_dict):
    weights = {"positive": 0, "neutral": 0, "negative": 0}
    for i, result in enumerate(aspect_results):
        aspect = list(weights_dict.keys())[i]
        weight = weights_dict.get(aspect, 1.0)
        for score in result:
            weights[score['label'].lower()] += score['score'] * weight
    total = sum(weights.values())
    return {k: round(v / total, 4) for k, v in weights.items() if total > 0}

# --- Label Mapping ---
label_map = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive"
}

# --- Load Sentiment Models ---
aspect_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
    top_k=None
)

overall_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
    top_k=None
)

# --- Generate Market Opinion ---
today = datetime.now().strftime("%B %d, %Y")
gemini_prompt = f"Give a detailed opinion about the stock market performance on {today}."

try:
    response = GEMINI.generate_content(gemini_prompt)
    generated_text = response.text.strip()
except Exception as e:
    print("Gemini API error:", e)
    generated_text = "Fallback opinion: The market showed mixed signals today, with tech stocks rising and energy falling."

# --- Sentiment Analysis ---
sentences = [preprocess(s) for s in generated_text.split('.') if s.strip()]

for sentence in sentences:
    print(f"\nAnalyzing: {sentence}")
    aspects = extract_aspects_nltk(sentence)

    if not aspects:
        print("  No aspects found. Skipping aspect-based sentiment.")
        continue

    aspect_weights = {aspect: 1 / len(aspects) for aspect in aspects}
    aspect_outputs = []

    for aspect in aspects:
        aspect_text = f"{sentence} [Aspect: {aspect}]"
        result = aspect_model(aspect_text)[0]
        aspect_outputs.append([
            {'label': label_map[r['label']], 'score': r['score']} for r in result
        ])
        print(f"  Aspect '{aspect}':")
        for r in result:
            print(f"    {label_map[r['label']]}: {round(r['score'], 4)}")

    overall_result = overall_model(sentence)[0]
    print("\nOverall sentiment:")
    for r in overall_result:
        print(f"  {label_map[r['label']]}: {round(r['score'], 4)}")

    top = max(overall_result, key=lambda x: x['score'])
    print(f"Most likely overall sentiment: {label_map[top['label']]} ({round(top['score'], 4)})")

    weighted = weighted_sentiment(aspect_outputs, aspect_weights)
    print("Weighted aspect sentiment:")
    for label, score in weighted.items():
        print(f"  {label}: {score}")
