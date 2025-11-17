"""
Test article extraction quality across different financial news publishers.

Tests both the extraction logic and the new 800-character minimum threshold.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from article_fetcher import extract_article_text, MIN_ARTICLE_LENGTH

# Test URLs from different publishers
test_publishers = {
    "SeekingAlpha": "https://seekingalpha.com/article/4836685-alphabet-rally-catches-up-to-reality",
    "Fool.com": "https://www.fool.com/investing/2025/10/31/why-wall-street-bullish-on-alphabet/",
    "Investing.com": "https://www.investing.com/analysis/alphabet-defies-the-trend-after-q3-beat-as-other-mag-7-names-disappoint-432SA-301031-2",
    "Benzinga": "https://www.benzinga.com/markets/equities/25/10/48554527/amazon-google-beyond-meat-investors-couldnt-stop-buying-these-3-stocks-on-friday",
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

print("=" * 80)
print("PUBLISHER EXTRACTION QUALITY TEST")
print(f"Minimum article length: {MIN_ARTICLE_LENGTH} chars")
print("=" * 80)

results = []

for publisher, url in test_publishers.items():
    print(f"\n{'=' * 80}")
    print(f"TESTING: {publisher}")
    print(f"URL: {url}")
    print("=" * 80)

    try:
        # Fetch HTML
        response = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=10,
            allow_redirects=True
        )

        if response.status_code != 200:
            print(f"  Status: {response.status_code} - FAILED")
            results.append((publisher, "FAILED", 0, f"HTTP {response.status_code}"))
            continue

        html_size = len(response.text)
        print(f"  Status: {response.status_code}")
        print(f"  Raw HTML: {html_size:,} chars")

        # Extract article
        article_text = extract_article_text(response.text, url)
        extracted_size = len(article_text)

        print(f"  Extracted: {extracted_size:,} chars")
        print(f"  Compression ratio: {html_size/max(extracted_size, 1):.1f}x")

        # Check against threshold
        meets_threshold = extracted_size >= MIN_ARTICLE_LENGTH
        status = "PASS" if meets_threshold else "TOO SHORT"

        print(f"  Quality threshold: {status}")

        if extracted_size > 0:
            print(f"\n  First 200 chars of extracted text:")
            print(f"  {'-' * 76}")
            preview = article_text[:200].replace('\n', ' ')
            print(f"  {preview}...")
            print(f"  {'-' * 76}")

        results.append((publisher, status, extracted_size, ""))

    except requests.Timeout:
        print("  ERROR: Timeout")
        results.append((publisher, "TIMEOUT", 0, "Request timeout"))

    except Exception as e:
        print(f"  ERROR: {e}")
        results.append((publisher, "ERROR", 0, str(e)[:50]))

# Summary
print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)
print(f"{'Publisher':<20} {'Status':<12} {'Chars':<10} {'Notes'}")
print("-" * 80)

for publisher, status, chars, notes in results:
    print(f"{publisher:<20} {status:<12} {chars:<10,} {notes}")

print("-" * 80)

pass_count = sum(1 for _, status, _, _ in results if status == "PASS")
print(f"\nPassed quality threshold: {pass_count}/{len(results)} publishers")
print(f"Minimum required: {MIN_ARTICLE_LENGTH} chars")
