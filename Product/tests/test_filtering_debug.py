"""
Debug script to test LLM filtering and see what's being rejected.
"""
import sys
import os
# Add parent directory to path to import Product modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
from cleaner import clean_company_and_ticker
from news_providers import fetch_recent_news
from llm_client import relevance_filter_batch

# Enable debug logging to see LLM decisions
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_filtering(company_input: str):
    """Test the filtering process and show what's being rejected."""
    print(f"\n{'='*80}")
    print(f"Testing filtering for: {company_input}")
    print(f"{'='*80}\n")

    # Step 1: Resolve company
    print("[1] Resolving company...")
    norm = clean_company_and_ticker(company_input)
    company = norm["company"]
    ticker = norm["ticker"]
    print(f"✓ Resolved: {company} ({ticker})\n")

    # Step 2: Fetch news
    print("[2] Fetching news from all providers...")
    df = fetch_recent_news(company, ticker, days=5, limit=60)

    if df.empty:
        print("❌ No articles fetched!")
        return

    print(f"✓ Fetched {len(df)} articles\n")

    # Show breakdown by provider
    provider_counts = df['provider'].value_counts()
    print("Articles by provider:")
    for provider, count in provider_counts.items():
        print(f"  - {provider}: {count}")
    print()

    # Step 3: Check descriptions
    print("[3] Checking description field coverage...")
    desc_stats = df.groupby('provider')['description'].apply(
        lambda x: f"{x.notna().sum()}/{len(x)} have descriptions"
    )
    for provider, stat in desc_stats.items():
        print(f"  - {provider}: {stat}")
    print()

    # Step 4: Show sample articles from each provider
    print("[4] Sample articles from each provider (before LLM filter):")
    for provider in df['provider'].unique():
        provider_df = df[df['provider'] == provider].head(3)
        print(f"\n  === {provider.upper()} ===")
        for idx, row in provider_df.iterrows():
            print(f"  Title: {row['title'][:100]}...")
            if row['description']:
                print(f"  Desc:  {row['description'][:100]}...")
            else:
                print(f"  Desc:  [MISSING]")
            print()

    # Step 5: Apply LLM filter with debug logging
    print("[5] Applying LLM filter (check DEBUG logs for YES/NO decisions)...")
    print("-" * 80)
    rows_for_filter = df[["title", "description"]].to_dict(orient="records")
    keep_flags = relevance_filter_batch(company, ticker, rows_for_filter, batch_size=10)
    print("-" * 80)

    # Step 6: Show results by provider
    df['passed_filter'] = keep_flags
    print("\n[6] Filter results by provider:")
    for provider in df['provider'].unique():
        provider_df = df[df['provider'] == provider]
        passed = provider_df['passed_filter'].sum()
        total = len(provider_df)
        percentage = (passed / total * 100) if total > 0 else 0
        print(f"  - {provider}: {passed}/{total} passed ({percentage:.1f}%)")

    # Step 7: Show rejected examples
    print("\n[7] Examples of REJECTED articles:")
    rejected_df = df[~df['passed_filter']].head(5)
    for idx, row in rejected_df.iterrows():
        print(f"\n  Provider: {row['provider']}")
        print(f"  Title: {row['title'][:100]}...")
        if row['description']:
            print(f"  Desc:  {row['description'][:150]}...")
        else:
            print(f"  Desc:  [MISSING]")

    print(f"\n{'='*80}")
    print(f"Summary: {sum(keep_flags)}/{len(df)} articles passed LLM filter")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Test with a company that should have news
    test_company = input("Enter company name to test: ").strip() or "Apple"
    test_filtering(test_company)
