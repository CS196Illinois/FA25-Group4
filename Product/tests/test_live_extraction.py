"""
Live test: Fetch real articles from current news and test extraction quality.
Uses actual Finnhub URLs that redirect to publisher sites.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime, timedelta
from config import FINNHUB_KEY
from article_fetcher import fetch_article_content, MIN_ARTICLE_LENGTH

if not FINNHUB_KEY:
    print("ERROR: FINNHUB_KEY not found")
    exit(1)

# Fetch recent Google news
end = datetime.now()
start = end - timedelta(days=5)

url = "https://finnhub.io/api/v1/company-news"
params = {
    "symbol": "GOOGL",
    "from": start.strftime("%Y-%m-%d"),
    "to": end.strftime("%Y-%m-%d"),
    "token": FINNHUB_KEY,
}

print("Fetching recent news from Finnhub...")
response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

articles = response.json()[:10]  # Test first 10 articles

print(f"Testing extraction on {len(articles)} articles")
print(f"Minimum threshold: {MIN_ARTICLE_LENGTH} chars")
print("=" * 80)

results = []

for i, article in enumerate(articles, 1):
    headline = article.get('headline', 'No headline')[:60]
    source = article.get('source', 'Unknown')
    finnhub_url = article.get('url', '')

    print(f"\n[{i}/{len(articles)}] {source}: {headline}...")
    print(f"URL: {finnhub_url}")

    # Fetch and extract
    full_text = fetch_article_content(finnhub_url)

    if full_text:
        char_count = len(full_text)
        status = "PASS" if char_count >= MIN_ARTICLE_LENGTH else f"TOO SHORT ({char_count} < {MIN_ARTICLE_LENGTH})"
        print(f"[OK] Extracted: {char_count:,} chars - {status}")

        # Show preview
        preview = full_text[:150].replace('\n', ' ')
        print(f"  Preview: {preview}...")

        results.append({
            'source': source,
            'headline': headline,
            'chars': char_count,
            'status': 'PASS' if char_count >= MIN_ARTICLE_LENGTH else 'TOO_SHORT',
        })
    else:
        print(f"[FAIL] Failed to extract (paywall/error/404)")
        results.append({
            'source': source,
            'headline': headline,
            'chars': 0,
            'status': 'FAILED',
        })

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

total = len(results)
passed = sum(1 for r in results if r['status'] == 'PASS')
too_short = sum(1 for r in results if r['status'] == 'TOO_SHORT')
failed = sum(1 for r in results if r['status'] == 'FAILED')

print(f"\nTotal articles tested: {total}")
print(f"  [OK] Passed threshold (>={MIN_ARTICLE_LENGTH} chars): {passed} ({passed/total*100:.0f}%)")
print(f"  [SHORT] Too short: {too_short} ({too_short/total*100:.0f}%)")
print(f"  [FAIL] Failed to extract: {failed} ({failed/total*100:.0f}%)")

if results:
    successful = [r for r in results if r['chars'] > 0]
    if successful:
        avg_chars = sum(r['chars'] for r in successful) / len(successful)
        print(f"\nAverage extracted length: {avg_chars:,.0f} chars")

print("\nCharacter distribution:")
for r in results:
    if r['chars'] > 0:
        bar_length = min(50, r['chars'] // 100)
        bar = '#' * bar_length
        print(f"  {r['chars']:>5,} chars {bar} {r['source']}")
