# --- Load Hugging Face Models ---
import os
import re
import torch
from dotenv import load_dotenv
from transformers import pipeline

# --- Text Preprocessing ---
def preprocess(text):
    text = text.lower()
    text = re.sub(r"http\S+", "", text)  # remove URLs
    text = re.sub(r"[^a-zA-Z\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text

# --- Label Mapping ---
label_map = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive"
}


# Keep this one
def weighted_sentiment(aspect_results, weights_dict):
    weights = {"positive": 0, "neutral": 0, "negative": 0}
    for i, result in enumerate(aspect_results):
        aspect = list(weights_dict.keys())[i]
        weight = weights_dict.get(aspect, 1.0)
        for score in result:
            weights[score['label'].lower()] += score['score'] * weight
    total = sum(weights.values())
    return {k: round(v / total, 4) for k, v in weights.items() if total > 0}


# --- Load Hugging Face Models ---
aspect_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
    return_all_scores=True
)

overall_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
    return_all_scores=True
)


# --- Weighted Sentiment from Aspects ---

# --- Main Analysis ---
# --- Multi-Sentence Analysis ---
# --- Main Analysis ---
sentence = preprocess("We had a great experience at the restaurant, food was delicious, but the service was kinda bad")

aspects = ["food", "service"]  # Define aspects before using them

aspect_outputs = []

for aspect in aspects:
    aspect_text = f"{sentence} [Aspect: {aspect}]"
    print(f"\nSentiment of aspect '{aspect}':")
    result = aspect_model(aspect_text)[0]
    aspect_outputs.append([
        {'label': label_map[r['label']], 'score': r['score']} for r in result
    ])

    for r in result:
        print(f"  {label_map[r['label']]}: {round(r['score'], 4)}")



# Hugging Face Overall Sentiment
print("\nOverall sentiment (Hugging Face):")
overall_result = overall_model(sentence)[0]
for r in overall_result:
    print(f"  {label_map[r['label']]}: {round(r['score'], 4)}")


top = max(overall_result, key=lambda x: x['score'])
print(f"\nMost likely overall sentiment: {label_map[top['label']]} ({round(top['score'], 4)})")


# Weighted Aspect Sentiment

aspect_weights = {"food": 0.6, "service": 0.4}

weighted = weighted_sentiment(aspect_outputs, aspect_weights)
print("\nWeighted overall sentiment (from aspects):")
for label, score in weighted.items():
    print(f"  {label}: {score}")
