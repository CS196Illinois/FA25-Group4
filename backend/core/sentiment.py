from transformers import pipeline

label_map = {
    "LABEL_0": "negative",
    "LABEL_1": "neutral",
    "LABEL_2": "positive"
}

sentiment_model = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment",
    top_k=None
)

def get_sentiment_scores(sentences):
    """
    Analyze sentiment for a list of sentences.

    Args:
        sentences: List of strings to analyze

    Returns:
        dict: Mapping of sentence -> sentiment score (positive - negative)
              Score ranges from -1.0 (very negative) to +1.0 (very positive)
    """
    scores = {}

    for sentence in sentences:
        result = sentiment_model(sentence)[0]

        # Extract positive and negative scores
        sentiment_dict = {}
        for r in result:
            label = label_map[r['label']]
            sentiment_dict[label] = r['score']

        # Calculate net sentiment: positive - negative
        net_score = sentiment_dict['positive'] - sentiment_dict['negative']
        scores[sentence] = round(net_score, 4)

    return scores
