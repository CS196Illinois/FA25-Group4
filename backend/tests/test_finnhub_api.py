"""
Test what URLs the Finnhub API actually returns.
"""
import sys
import os
# Add parent directory to path to import Product modules


import requests
import json
from datetime import datetime, timedelta
from config import FINNHUB_KEY

if not FINNHUB_KEY:
    print("ERROR: FINNHUB_KEY not found in environment")
    exit(1)

# Fetch Google news from Finnhub
end = datetime.now()
start = end - timedelta(days=5)

url = "https://finnhub.io/api/v1/company-news"
params = {
    "symbol": "GOOGL",
    "from": start.strftime("%Y-%m-%d"),
    "to": end.strftime("%Y-%m-%d"),
    "token": FINNHUB_KEY,
}

print("Fetching from Finnhub API...")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

data = response.json()

print(f"Received {len(data)} articles\n")
print("=" * 80)

# Show first 3 articles in detail
for i, article in enumerate(data[:3], 1):
    print(f"\nARTICLE {i}")
    print("=" * 80)
    print(json.dumps(article, indent=2))
    print("\nKey observations:")
    print(f"  - 'url' field: {article.get('url', 'MISSING')}")
    print(f"  - 'id' field: {article.get('id', 'MISSING')}")
    print(f"  - 'headline': {article.get('headline', 'MISSING')[:60]}...")
    print("=" * 80)
