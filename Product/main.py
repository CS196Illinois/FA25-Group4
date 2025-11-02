import logging
from cleaner import clean_company_and_ticker
from news_providers import fetch_recent_news
from llm_client import relevance_filter_batch
from summarize import summarize_and_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_NEWS_DAYS = 5
DEFAULT_NEWS_LIMIT = 60
LLM_BATCH_SIZE = 10
MAX_HEADLINES_FOR_SUMMARY = 20
MAX_HEADLINES_TO_DISPLAY = 12

def run_cli():
    """Main CLI entry point for the investment news aggregation tool."""
    print("=== Simple Invest News (Strict v3) ===")

    # Get user input with validation
    user_company = input("Enter a company: ").strip()
    if not user_company:
        print("Error: Company name cannot be empty.")
        logger.error("User provided empty company name")
        return

    goal_raw = input("Goal? (short-term / long-term): ").strip().lower()
    goal = "short-term" if "short" in goal_raw else "long-term"

    try:
        # Step 1: Resolve entity
        logger.info(f"Resolving company name: {user_company}")
        print("\n[1/4] Resolving company name and ticker...")

        norm = clean_company_and_ticker(user_company)
        company, ticker = norm["company"], norm["ticker"]

        if not company:
            print("Error: Could not resolve company name.")
            logger.error(f"Failed to resolve company: {user_company}")
            return

        print(f"✓ Normalized: {company}" + (f" ({ticker})" if ticker else " (no ticker)"))
        logger.info(f"Resolved to: {company} ({ticker})")

        # Step 2: Fetch news
        print(f"\n[2/4] Fetching recent news from providers (last {DEFAULT_NEWS_DAYS} days)...")
        logger.info(f"Fetching news for {company} ({ticker})")

        df = fetch_recent_news(company, ticker, days=DEFAULT_NEWS_DAYS, limit=DEFAULT_NEWS_LIMIT)

        if df.empty:
            print("\nNo headlines found from any provider.")
            print("This could be due to:")
            print("  - Network connectivity issues")
            print("  - Missing or invalid API keys in .env file")
            print("  - No recent news for this company")
            logger.warning(f"No news found for {company}")
            return

        print(f"✓ Found {len(df)} headlines from providers")
        logger.info(f"Fetched {len(df)} headlines")

        # Step 3: LLM relevance filter (no literal filter - AI evaluates all headlines)
        print(f"\n[3/4] Applying AI relevance verification on {len(df)} headlines...")
        print("      (Using batched processing, may take 5-10 seconds)")
        logger.info(f"Starting LLM relevance filter for {len(df)} headlines")

        rows_for_filter = df[["title", "description"]].to_dict(orient="records")
        keep_flags = relevance_filter_batch(company, ticker, rows_for_filter, batch_size=LLM_BATCH_SIZE)
        df = df[keep_flags].reset_index(drop=True)

        if df.empty:
            print("\nNo relevant headlines after AI verification.")
            print("The AI determined none of the headlines were truly about this company.")
            logger.warning("No headlines passed LLM filter")
            return

        print(f"✓ {len(df)} headlines verified as relevant by AI")
        logger.info(f"{len(df)} headlines after LLM filter")

        # Step 4: Summarize + stance
        print(f"\n[4/4] Generating investment summary...")
        logger.info("Generating summary and sentiment")

        summary = summarize_and_score(company, ticker, goal, df.to_dict(orient="records"))
        print(f"✓ Summary generated")

        # Pretty-print results
        print("\n" + "="*60)
        print("--- Investor Bullets ---")
        for b in summary["bullets"]:
            print(f"  • {b}")

        print("\n--- Long Summary ---")
        print(f"  {summary['long']}")

        print("\n--- Investment Sentiment ---")
        print(f"  Stance: {summary['stance']} | Score: {summary['score']}/9")
        print(f"  (1=very negative, 5=neutral, 9=very positive)")
        if summary["reason"]:
            print(f"  Reason: {summary['reason']}")

        print("\n--- Relevant Headlines (newest first) ---")
        show = df[["date", "source", "title", "url"]].copy()
        try:
            show["date"] = show["date"].dt.strftime("%Y-%m-%d %H:%M UTC")
        except Exception as e:
            logger.warning(f"Date formatting failed: {e}")
            pass

        for _, r in show.head(MAX_HEADLINES_TO_DISPLAY).iterrows():
            print(f"\n  [{r['date']}] {r['source']}")
            print(f"  {r['title']}")
            print(f"  {r['url']}")

        print("\n" + "="*60)
        print("(Disclaimer: Informational only. This is NOT personalized investment advice.)")
        logger.info("CLI execution completed successfully")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        logger.info("User cancelled operation")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error in CLI: {str(e)}", exc_info=True)
        print("\nPlease check:")
        print("  1. Your .env file has valid API keys (especially GEMINI_KEY)")
        print("  2. You have internet connectivity")
        print("  3. The company name is valid")

if __name__ == "__main__":
    run_cli()
