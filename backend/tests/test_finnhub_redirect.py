"""
Test if Finnhub proxy URLs redirect to original articles.
"""
import requests

finnhub_url = "https://finnhub.io/api/news?id=567decbe07f212a8c815a51fb6043915df97edb8efacc1e96454750c66f70968"

print(f"Testing URL: {finnhub_url}\n")

try:
    response = requests.get(
        finnhub_url,
        headers={
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        timeout=10,
        allow_redirects=True
    )

    print(f"Status Code: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Number of redirects: {len(response.history)}")

    if response.history:
        print("\nRedirect chain:")
        for i, resp in enumerate(response.history, 1):
            print(f"  {i}. {resp.status_code} -> {resp.url}")
        print(f"  Final: {response.status_code} -> {response.url}")

    print(f"\nContent-Type: {response.headers.get('Content-Type', 'unknown')}")
    print(f"Content length: {len(response.text)} chars")

    # Check if it's HTML
    if 'html' in response.headers.get('Content-Type', ''):
        print("\nFirst 300 chars of HTML:")
        print("-" * 60)
        print(response.text[:300])
        print("-" * 60)

except Exception as e:
    print(f"Error: {e}")
