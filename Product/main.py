import logging
from cleaner import clean_company_and_ticker
from news_providers import fetch_recent_news
from llm_client import relevance_filter_batch
from article_fetcher import fetch_articles_batch
from summarize import summarize_and_score
from quotes import extract_quotes_from_articles, print_quotes, get_quote_stats

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
    print("=== Simple Invest News (Full Article Analysis) ===")

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
        print("\n[1/5] Resolving company name and ticker...")

        norm = clean_company_and_ticker(user_company)
        company = norm["company"]
        ticker = norm["ticker"]
        needs_confirmation = norm.get("needs_confirmation", False)
        candidates = norm.get("candidates")
        confidence = norm.get("confidence", 0)

        if not company:
            print("Error: Could not resolve company name.")
            logger.error(f"Failed to resolve company: {user_company}")
            return

        # Handle user confirmation if needed
        if needs_confirmation and candidates:
            print(f"\nMultiple matches found (AI confidence: {confidence}%). Please select:")
            for i, cand in enumerate(candidates, 1):
                validated_mark = "" if cand.get("validated", True) else " [UNVALIDATED]"
                print(f"  [{i}] {cand['company']} ({cand['ticker']}){validated_mark}")
            print(f"  [{len(candidates)+1}] Enter ticker manually")
            print(f"  [0] Cancel")

            while True:
                try:
                    choice = input("\nYour choice: ").strip()
                    choice_num = int(choice)

                    if choice_num == 0:
                        print("Operation cancelled.")
                        logger.info("User cancelled after seeing candidates")
                        return
                    elif 1 <= choice_num <= len(candidates):
                        selected = candidates[choice_num - 1]
                        company = selected["company"]
                        ticker = selected["ticker"]
                        logger.info(f"User selected candidate {choice_num}: {company} ({ticker})")
                        break
                    elif choice_num == len(candidates) + 1:
                        # Manual entry
                        company = input("Enter company name: ").strip()
                        ticker = input("Enter ticker symbol: ").strip().upper()
                        if company and ticker:
                            logger.info(f"User manually entered: {company} ({ticker})")
                            break
                        else:
                            print("Error: Both company name and ticker are required.")
                    else:
                        print(f"Please enter a number between 0 and {len(candidates)+1}")
                except ValueError:
                    print("Please enter a valid number")
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled by user.")
                    return

        elif needs_confirmation and not candidates:
            # Low confidence, no candidates found
            print(f"\nWarning: Could not confidently resolve '{user_company}' (confidence: {confidence}%)")
            print("Options:")
            print("  [1] Enter ticker manually")
            print("  [0] Cancel")

            while True:
                try:
                    choice = input("\nYour choice: ").strip()
                    if choice == "0":
                        print("Operation cancelled.")
                        logger.info("User cancelled due to low confidence")
                        return
                    elif choice == "1":
                        company = input("Enter company name: ").strip()
                        ticker = input("Enter ticker symbol: ").strip().upper()
                        if company and ticker:
                            logger.info(f"User manually entered: {company} ({ticker})")
                            break
                        else:
                            print("Error: Both company name and ticker are required.")
                    else:
                        print("Please enter 0 or 1")
                except KeyboardInterrupt:
                    print("\n\nOperation cancelled by user.")
                    return

        print(f"✓ Normalized: {company}" + (f" ({ticker})" if ticker else " (no ticker)"))
        logger.info(f"Resolved to: {company} ({ticker})")

        # Step 2: Fetch news
        print(f"\n[2/5] Fetching recent news from providers (last {DEFAULT_NEWS_DAYS} days)...")
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
        print(f"\n[3/5] Applying AI relevance verification on {len(df)} headlines...")
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

        # Step 3.5: Fetch full article content (NEW)
        print(f"\n[3.5/5] Fetching full article content for deeper analysis...")
        print(f"         (This may take 20-30 seconds for {len(df)} articles)")
        logger.info(f"Fetching full article content for {len(df)} articles")

        rows_with_content = fetch_articles_batch(df.to_dict(orient="records"))

        # Count how many articles successfully fetched
        articles_fetched = sum(1 for r in rows_with_content if r.get('full_text'))
        print(f"✓ Fetched full content for {articles_fetched}/{len(df)} articles")
        logger.info(f"Successfully fetched {articles_fetched} full articles")

        # Step 4: Extract key quotes (second analysis branch)
        print(f"\n[4/6] Extracting most important investment-relevant quotes...")
        logger.info("Extracting quotes from articles")

        quotes = extract_quotes_from_articles(rows_with_content, company, num_quotes=15)
        print(f"✓ Extracted {len(quotes)} key quotes" if quotes else "✓ No quotes extracted")
        logger.info(f"Extracted {len(quotes)} quotes")

        # Step 5: Summarize + stance (parallel analysis branch)
        print(f"\n[5/6] Generating investment summary with full article analysis...")
        logger.info("Generating summary and sentiment")

        summary = summarize_and_score(company, ticker, goal, rows_with_content)

        print(f"\n[6/6] Analysis complete!")
        print(f"✓ Summary generated based on {articles_fetched} full articles")

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

        # Display extracted quotes
        if quotes:
            print("\n--- Key Investment Quotes ---")
            # Show top 8 quotes
            for i, q in enumerate(quotes[:8], 1):
                weight_blocks = int(q["weight"] * 10)
                weight_bar = "█" * weight_blocks + "░" * (10 - weight_blocks)
                print(f"\n  {i}. [{weight_bar}] {q['weight']:.2f}")
                print(f"     \"{q['quote']}\"")
                print(f"     — {q['speaker']}")
                print(f"     Why: {q['context']}")

            # Show quote statistics
            stats = get_quote_stats(quotes)
            print(f"\n  Stats: {stats['critical_count']} critical (≥0.9), {stats['high_count']} high priority (≥0.7)")
            if stats['top_speakers']:
                print(f"  Most quoted: {', '.join(stats['top_speakers'][:2])}")

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
        print(f"\nERROR: An unexpected error occurred: {str(e)}")
        logger.error(f"Unexpected error in CLI: {str(e)}", exc_info=True)
        print("\nPlease check:")
        print("  1. Your .env file has valid API keys (especially GEMINI_KEY)")
        print("  2. You have internet connectivity")
        print("  3. The company name is valid")

def run_analysis(company_name: str, goal: str = "short-term") -> dict:
    """
    Programmatic entry point for investment news analysis.

    Args:
        company_name: Company name to analyze
        goal: Investment timeframe - "short-term" or "long-term"

    Returns:
        Dictionary with analysis results:
        {
            "success": bool,
            "company": str,
            "ticker": str,
            "bullets": list[str],
            "long_summary": str,
            "stance": str,
            "score": int,
            "reason": str,
            "quotes": list[dict],
            "headlines": list[dict],
            "error": str (if success=False)
        }
    """
    try:
        if not company_name or not company_name.strip():
            return {
                "success": False,
                "error": "Company name cannot be empty"
            }

        # Step 1: Resolve entity
        logger.info(f"Resolving company name: {company_name}")
        norm = clean_company_and_ticker(company_name)
        company = norm["company"]
        ticker = norm["ticker"]

        if not company:
            return {
                "success": False,
                "error": f"Could not resolve company name: {company_name}"
            }

        logger.info(f"Resolved to: {company} ({ticker})")

        # Step 2: Fetch news
        logger.info(f"Fetching news for {company} ({ticker})")
        df = fetch_recent_news(company, ticker, days=DEFAULT_NEWS_DAYS, limit=DEFAULT_NEWS_LIMIT)

        if df.empty:
            return {
                "success": False,
                "error": "No headlines found from any provider"
            }

        logger.info(f"Fetched {len(df)} headlines")

        # Step 3: LLM relevance filter
        logger.info(f"Starting LLM relevance filter for {len(df)} headlines")
        rows_for_filter = df[["title", "description"]].to_dict(orient="records")
        keep_flags = relevance_filter_batch(company, ticker, rows_for_filter, batch_size=LLM_BATCH_SIZE)
        df = df[keep_flags].reset_index(drop=True)

        if df.empty:
            return {
                "success": False,
                "error": "No relevant headlines after AI verification"
            }

        logger.info(f"{len(df)} headlines after LLM filter")

        # Step 4: Fetch full article content
        logger.info(f"Fetching full article content for {len(df)} articles")
        rows_with_content = fetch_articles_batch(df.to_dict(orient="records"))
        articles_fetched = sum(1 for r in rows_with_content if r.get('full_text'))
        logger.info(f"Successfully fetched {articles_fetched} full articles")

        # Step 5: Extract key quotes
        logger.info("Extracting quotes from articles")
        quotes = extract_quotes_from_articles(rows_with_content, company, num_quotes=15)
        logger.info(f"Extracted {len(quotes)} quotes")

        # Step 6: Summarize + stance
        logger.info("Generating summary and sentiment")
        summary = summarize_and_score(company, ticker, goal, rows_with_content)

        # Format headlines for output
        headlines = []
        for _, row in df.head(MAX_HEADLINES_TO_DISPLAY).iterrows():
            try:
                date_str = row['date'].strftime("%Y-%m-%d %H:%M UTC")
            except:
                date_str = str(row['date'])

            headlines.append({
                "date": date_str,
                "source": row['source'],
                "title": row['title'],
                "url": row['url']
            })

        logger.info("Analysis completed successfully")

        return {
            "success": True,
            "company": company,
            "ticker": ticker,
            "bullets": summary["bullets"],
            "long_summary": summary["long"],
            "stance": summary["stance"],
            "score": summary["score"],
            "reason": summary.get("reason", ""),
            "quotes": quotes[:8] if quotes else [],  # Top 8 quotes
            "headlines": headlines,
            "articles_analyzed": articles_fetched
        }

    except Exception as e:
        logger.error(f"Error in run_analysis: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }


if __name__ == "__main__":
    run_cli()
