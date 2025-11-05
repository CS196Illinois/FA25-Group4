"""
Test article extraction for low character count articles.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from article_fetcher import extract_article_text

# This article had only 536 chars extracted
test_url = "https://finnhub.io/api/news?id=68a932ffbecae9f51cfd86c34a6c1"

print(f"Testing low-count article URL:\n{test_url}\n")
print("=" * 80)

try:
    response = requests.get(
        test_url,
        headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        timeout=10,
        allow_redirects=True
    )

    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Redirects: {len(response.history)}")
    print(f"HTML size: {len(response.text)} chars")
    print()

    # Extract article
    article_text = extract_article_text(response.text, test_url)

    print(f"Extracted: {len(article_text)} chars")
    print("=" * 80)
    print("FULL EXTRACTED TEXT:")
    print("=" * 80)
    print(article_text)
    print("=" * 80)

    # Also show a sample of the HTML to see what we're working with
    print("\nSample of raw HTML (first 1000 chars after <body>):")
    print("-" * 80)
    body_start = response.text.find('<body')
    if body_start != -1:
        print(response.text[body_start:body_start+1000])
    print("-" * 80)

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
