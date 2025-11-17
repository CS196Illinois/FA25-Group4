"""
Diagnostic script to inspect Finnhub URLs and article extraction.

Run this to see what's actually being fetched from Finnhub API endpoints.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from article_fetcher import extract_article_text

# Example URLs from the logs with different char counts
test_urls = {
    "high_count": "https://finnhub.io/api/news?id=567decbe07f212a8c815a51fb6043",  # 3080 chars
    "low_count": "https://finnhub.io/api/news?id=68a932ffbecae9f51cfd86c34a6c1",   # 536 chars
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

print("=" * 80)
print("FINNHUB URL DIAGNOSTIC")
print("=" * 80)

for label, url in test_urls.items():
    print(f"\n{'=' * 80}")
    print(f"Testing: {label.upper()}")
    print(f"URL: {url}")
    print("=" * 80)

    try:
        # Fetch the URL
        response = requests.get(
            url,
            headers={
                'User-Agent': USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml',
            },
            timeout=10,
            allow_redirects=True
        )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Final URL after redirects: {response.url}")
        print(f"Raw HTML length: {len(response.text)} chars")

        # Show first 500 chars of HTML
        print(f"\nFirst 500 chars of HTML:")
        print("-" * 80)
        print(response.text[:500])
        print("-" * 80)

        # Extract article text
        article_text = extract_article_text(response.text, url)
        print(f"\nExtracted article text: {len(article_text)} chars")

        if article_text:
            print(f"\nFirst 300 chars of extracted text:")
            print("-" * 80)
            print(article_text[:300])
            print("-" * 80)
        else:
            print("\n⚠️  No article text extracted!")

    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
