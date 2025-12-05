# --- Imports ---
import os
import re
import requests
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
    return {k: round(v / total, 2) for k, v in weights.items() if total > 0}



def classify_sentiment(weighted_scores):
    # Pick the label with the highest decimal score
    return max(weighted_scores, key=weighted_scores.get)



# --- New helper function: dynamic ticker resolver ---
def resolve_ticker(user_input: str) -> dict:
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={user_input}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "quotes" in data and len(data["quotes"]) > 0:
            first = data["quotes"][0]
            return {
                "company": first.get("longname", user_input),
                "ticker": first.get("symbol", "")   # <-- make sure you capture the symbol here
            }
    return {"company": user_input, "ticker": ""}


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

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------

def analyze_quote_sentiment(quote_text):
    """
    Analyze sentiment of a single quote using aspect-based and overall models.

    Args:
        quote_text: The quote string

    Returns:
        Dictionary with sentiment details:
        {
            "overall_sentiment": "positive" | "neutral" | "negative",
            "weighted_sentiment": { "positive": float, "neutral": float, "negative": float },
            "top_label": str
        }
    """
    sentence = preprocess(quote_text)
    aspects = extract_aspects_nltk(sentence)

    if not aspects:
        return {
            "overall_sentiment": "neutral",
            "weighted_sentiment": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
            "top_label": "neutral"
        }

    aspect_weights = {aspect: 1 / len(aspects) for aspect in aspects}
    aspect_outputs = []

    for aspect in aspects:
        aspect_text = f"{sentence} [Aspect: {aspect}]"
        result = aspect_model(aspect_text)[0]
        aspect_outputs.append([
            {'label': label_map[r['label']], 'score': r['score']} for r in result
        ])

    overall_result = overall_model(sentence)[0]
    top = max(overall_result, key=lambda x: x['score'])

    weighted = weighted_sentiment(aspect_outputs, aspect_weights)
    top_label = classify_sentiment(weighted)

    return {
        "overall_sentiment": top_label,
        "weighted_sentiment": weighted,
        "top_label": top_label
}

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------

import re

def answer_question_with_quotes(question: str, quotes: list) -> str:
    """
    Answer a question using the quotes dataset and their sentiment analysis.
    Args:
        question: The user question string
        quotes: List of quote dicts with keys ["quote", "sentiment", "sentiment_details"]
    Returns:
        A summary answer string
    """
    # Step 1: Extract keywords (ignore very short words)
    keywords = [w.lower() for w in question.split() if len(w) > 3]

    # Step 2: Find relevant quotes using regex search
    relevant_quotes = []
    for q in quotes:
        text = q["quote"].lower()
        if any(re.search(kw, text) for kw in keywords):
            relevant_quotes.append(q)

    # Step 3: Handle case where no quotes match
    if not relevant_quotes:
        return "No relevant quotes found to answer your question."

    # Step 4: Aggregate sentiment counts
        # Step 4: Aggregate sentiment scores (decimals)
    sentiment_totals = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    for q in relevant_quotes:
        for k, v in q["sentiment_details"]["weighted_sentiment"].items():
            sentiment_totals[k] += v

    # Normalize by number of quotes
    num_quotes = len(relevant_quotes)
    sentiment_avg = {k: round(v / num_quotes, 2) for k, v in sentiment_totals.items()}


    # Step 5: Build summary answer
    summary = (
        f"Out of {num_quotes} relevant quotes:\n"
        f"- Positive: {sentiment_avg['positive']}\n"
        f"- Neutral: {sentiment_avg['neutral']}\n"
        f"- Negative: {sentiment_avg['negative']}\n"
    )


    # Step 6: Add a few examples
    for q in relevant_quotes[:3]:
        summary += f'\nExample: "{q["quote"]}" → {q["sentiment"]}'

    return summary

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------------

# --- New helper function ---
from Product.cleaner import clean_company_and_ticker
from Product.news_providers import fetch_recent_news
from Product.quotes import extract_quotes_from_articles, print_quotes, get_quote_stats, fallback_extract_quotes
from Product.config import GEMINI


if __name__ == "__main__":
    # Step 1: User input
    user_input = input("Enter a company name or ticker: ")
    resolved = resolve_ticker(user_input)   # use dynamic lookup instead of hard-coded map
    company_name = resolved["company"]
    ticker = resolved["ticker"]
    print(f"Resolved company: {company_name}, ticker: {ticker}")



    # Step 2: Fetch recent news
    query = ticker if ticker else company_name
    df = fetch_recent_news(company=company_name, ticker=ticker, days=5, limit=50)
    for _, row in df.iterrows():
        print("Article:", row.get("title"))


    # Step 3: Convert DataFrame to article dicts
    articles = []
    for _, row in df.iterrows():
        articles.append({
            "full_text": row.get("description", ""),
            "title": row.get("title", ""),
            "source": row.get("source", ""),
            "url": row.get("url", ""),
            "date": row.get("date", datetime.now())
        })

    # Step 4: Extract quotes
    quotes = extract_quotes_from_articles(articles, company_name)

    # 👉 Add fallback here
    if not quotes:
        print(f"No quotes extracted for {company_name} ({ticker}). Running sentiment on article descriptions instead...")
        quotes = []
        for article in articles:
            sentiment_result = analyze_quote_sentiment(article["full_text"])
            quotes.append({
                "quote": article["full_text"],
                "sentiment": sentiment_result["top_label"],
                "sentiment_details": sentiment_result,
                "ticker": ticker,
                "speaker": "Unknown",
                "weight": 0.5,
                "context": "Sentiment derived from article text",
                "source_article": {
                    "title": article.get("title", ""),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "date": article.get("date")
            }
        })


if not quotes:
    print(f"No quotes extracted for {company_name} ({ticker}).")
else:
    # Step 5: Enrich with sentiment + attach ticker
    for quote in quotes:
        sentiment_result = analyze_quote_sentiment(quote["quote"])
        quote["sentiment"] = sentiment_result["top_label"]
        quote["sentiment_details"] = sentiment_result
        quote["ticker"] = ticker


        # Step 6: Print quotes and stats
        print_quotes(quotes)
        stats = get_quote_stats(quotes)
        print("Quote Stats:", stats)

        # Step 7: Answer a question
        question = f"What is the sentiment around {company_name}'s earnings?"
        print(answer_question_with_quotes(question, quotes))
