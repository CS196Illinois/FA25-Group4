import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentiment import get_sentiment_scores

# Test cases organized by expected sentiment type
TEST_CASES = {
    "Positive Sentiment": [
        "Apple stock is soaring to new heights!",
        "Company reports record-breaking quarterly earnings.",
        "Investors are optimistic about the tech sector's future.",
        "Stock price surged 25% following the acquisition announcement.",
        "Analysts upgraded the rating to strong buy."
    ],

    "Negative Sentiment": [
        "The market crashed today amid recession fears.",
        "Company files for bankruptcy protection.",
        "Stock plummets after disappointing earnings report.",
        "Investors flee as fraud allegations surface.",
        "Massive layoffs announced, stock price tanks."
    ],

    "Neutral Sentiment": [
        "Trading volumes remained steady with no major changes.",
        "The company announced a routine dividend payment.",
        "Market closed flat after a quiet trading session.",
        "Stock price unchanged following the announcement.",
        "Analysts maintained their hold rating on the stock."
    ],

    "Mixed/Complex Sentiment": [
        "Despite strong earnings, the stock fell due to weak guidance.",
        "Revenue grew but profits declined compared to last year.",
        "The acquisition brings opportunities but also significant risks.",
        "While sales increased, the company faces regulatory challenges.",
        "Stock price recovered slightly after yesterday's massive drop."
    ]
}


def interpret_score(score):
    """Convert numeric score to sentiment label."""
    if score > 0.3:
        return "POSITIVE"
    elif score < -0.3:
        return "NEGATIVE"
    else:
        return "NEUTRAL"


if __name__ == "__main__":
    print("=" * 80)
    print("SENTIMENT ANALYSIS TEST")
    print("=" * 80)

    for category, sentences in TEST_CASES.items():
        print(f"\n{'=' * 80}")
        print(f"{category.upper()}")
        print("=" * 80)

        # Get sentiment scores for this category
        scores = get_sentiment_scores(sentences)

        for sentence, score in scores.items():
            sentiment = interpret_score(score)

            # Color-coded output based on sentiment
            if sentiment == "POSITIVE":
                indicator = "✓ [+]"
            elif sentiment == "NEGATIVE":
                indicator = "✗ [-]"
            else:
                indicator = "● [~]"

            print(f"\n{indicator} Score: {score:+.4f} | {sentiment}")
            print(f"    Text: {sentence}")

        print()

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nScore Interpretation:")
    print("  > +0.3  = Positive sentiment")
    print("  -0.3 to +0.3 = Neutral sentiment")
    print("  < -0.3  = Negative sentiment")
