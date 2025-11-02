from cleaner import clean_company_and_ticker
from news_providers import fetch_recent_news
from filters import apply_literal_filter
from llm_client import relevance_filter_batch
from summarize import summarize_and_score

def run_cli():
    print("=== Simple Invest News (Strict v3) ===")
    user_company = input("Enter a company: ").strip()
    goal_raw = input("Goal? (short-term / long-term): ").strip().lower()
    goal = "short-term" if "short" in goal_raw else "long-term"

    # Step 1: resolve entity
    norm = clean_company_and_ticker(user_company)
    company, ticker = norm["company"], norm["ticker"]
    print(f"\nNormalized: {company}" + (f" ({ticker})" if ticker else " (no ticker)"))

    # Step 2: fetch news
    df = fetch_recent_news(company, ticker, days=5, limit=60)

    if df.empty:
        print("\nNo headlines from providers.")
        return

    # Step 3: cheap literal filter
    df = apply_literal_filter(df, company, ticker)
    if df.empty:
        print("\nNo relevant headlines after literal filter.")
        return

    # Step 4: LLM relevance filter (strict yes/no; fail-closed)
    rows_for_filter = df[["title", "description"]].to_dict(orient="records")
    keep_flags = relevance_filter_batch(company, ticker, rows_for_filter, batch_size=10)
    df = df[keep_flags].reset_index(drop=True)

    if df.empty:
        print("\nNo relevant headlines after strict LLM filter.")
        return

    # Step 5: summarize + stance
    summary = summarize_and_score(company, ticker, goal, df.to_dict(orient="records"))

    # Step 6: pretty-print
    print("\n--- Investor Bullets ---")
    for b in summary["bullets"]:
        print(f"- {b}")

    print("\n--- Long Summary ---")
    print(summary["long"])

    print("\n--- Invest Sentiment ---")
    print(f"Stance: {summary['stance']} | Score: {summary['score']} (1=very negative, 9=very positive)")
    if summary["reason"]:
        print(f"Reason: {summary['reason']}")

    print("\n--- Relevant Headlines (newest) ---")
    show = df[["date", "source", "title", "url"]].copy()
    try:
        show["date"] = show["date"].dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        pass
    for _, r in show.head(12).iterrows():
        print(f"[{r['date']}] {r['source']}: {r['title']}\n  {r['url']}")

    print("\n(Disclaimer: Informational only. This is NOT personalized investment advice.)")

if __name__ == "__main__":
    run_cli()
