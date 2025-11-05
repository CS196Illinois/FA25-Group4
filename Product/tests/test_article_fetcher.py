"""
Simple test for article fetching functionality.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
from article_fetcher import fetch_article_content, fetch_articles_batch

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_single_article():
    """Test fetching a single article."""
    print("\n" + "="*80)
    print("Test 1: Fetch a single article")
    print("="*80)

    # Test with a known financial news URL (Reuters is usually accessible)
    test_url = "https://www.reuters.com/sustainability/boards-policy-regulation/berkshire-profit-rises-cash-soars-record-2025-11-01/"

    print(f"\nFetching: {test_url}")
    content = fetch_article_content(test_url)

    if content:
        print(f"\n[SUCCESS] Successfully fetched article!")
        print(f"Content length: {len(content)} characters")
        print(f"\nFirst 300 characters:")
        print("-" * 80)
        print(content[:300] + "...")
        print("-" * 80)
    else:
        print(f"\n[FAILED] Failed to fetch article (may be paywalled or not accessible)")


def test_batch_fetching():
    """Test batch fetching with mock data."""
    print("\n" + "="*80)
    print("Test 2: Batch fetch multiple articles")
    print("="*80)

    # Create mock news items (use placeholder URLs for testing)
    mock_articles = [
        {
            "title": "Test Article 1",
            "source": "Reuters",
            "url": "https://www.reuters.com/markets/us/",
            "description": "Test description 1"
        },
        {
            "title": "Test Article 2",
            "source": "Bloomberg",
            "url": "https://www.bloomberg.com/markets",
            "description": "Test description 2"
        },
        {
            "title": "Test Article 3 (invalid URL)",
            "source": "Test",
            "url": "https://invalid-url-that-does-not-exist.com/article",
            "description": "Test description 3"
        }
    ]

    print(f"\nAttempting to fetch {len(mock_articles)} articles...")
    enriched = fetch_articles_batch(mock_articles)

    print(f"\n{'='*80}")
    print("Results:")
    print(f"{'='*80}")

    for i, article in enumerate(enriched, 1):
        has_content = bool(article.get('full_text'))
        status = "[SUCCESS]" if has_content else "[FAILED]"
        content_len = len(article.get('full_text', '')) if has_content else 0

        print(f"\nArticle {i}: {status}")
        print(f"  Title: {article['title']}")
        print(f"  URL: {article['url']}")
        print(f"  Content length: {content_len} chars")

        if has_content:
            preview = article['full_text'][:150]
            print(f"  Preview: {preview}...")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Article Fetcher Test Suite")
    print("="*80)

    print("\nNote: Some tests may fail if URLs are paywalled or inaccessible.")
    print("This is expected behavior (fail-closed approach).\n")

    # Run tests
    test_single_article()
    test_batch_fetching()

    print("\n" + "="*80)
    print("Tests complete!")
    print("="*80 + "\n")
