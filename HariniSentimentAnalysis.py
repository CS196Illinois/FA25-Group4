from transformers import pipeline
import torch

# Load aspect-based sentiment analysis model
aspect_model = pipeline(
    "text-classification",
    model="yangheng/deberta-v3-base-absa-v1.1",
    tokenizer="yangheng/deberta-v3-base-absa-v1.1",
    return_all_scores=True
)

# Load overall sentiment model
overall_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-xlm-roberta-base-sentiment",
    return_all_scores=True
)

# Input sentence and aspects
sentence = "We had a great experience at the restaurant, food was delicious, but the service was kinda bad"
aspects = ["food", "service"]

# Analyze aspect-based sentiment
for aspect in aspects:
    print(f"\nSentiment of aspect '{aspect}':")
    result = aspect_model(f"{sentence} [ASP] {aspect}")
    for score in result[0]:
        print(f"  {score['label']}: {round(score['score'], 4)}")

# Analyze overall sentiment
print("\nOverall sentiment:")
overall_result = overall_model(sentence)[0]
for score in overall_result:
    print(f"  {score['label']}: {round(score['score'], 4)}")

# Print most likely overall sentiment
top_sentiment = max(overall_result, key=lambda x: x['score'])
print(f"\nMost likely overall sentiment: {top_sentiment['label']} ({round(top_sentiment['score'], 4)})")
