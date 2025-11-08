from cleaner import clean_company_and_ticker
from summarizer import summarize_and_score
from SentimentAnalysis_Update_1 import analyze_sentiment
from config import GEMINI
from utils import utc_today

def run_market_analysis(user_input: str, goal: str, headlines: list):
    # Step 1: Resolve company and ticker
    resolved = clean_company_and_ticker(user_input)
    company = resolved["company"]
    ticker = resolved["ticker"]



    # Step 2: Filter relevant headlines
def gemini_yes_no_company(company: str, ticker: str, title: str, desc: str) -> bool:
    """
    Uses Gemini to determine if a headline is about the target company.
    Returns True only if Gemini responds with 'YES'.
    """
    prompt = (
        f"Answer YES or NO. Is this headline about the COMPANY {company} (ticker {ticker}), "
        "its business/stock/products/execs/financials—NOT unrelated firms?\n"
        f"Headline: {title[:300]}\nDescription: {desc[:500]}\nOnly YES or NO:"
    )
    try:
        response = GEMINI.generate_content(prompt)
        return "YES" in (response.text or "").strip().upper()
    except Exception:
        return False  # fail closed

# Now this block is OUTSIDE the function
relevant = []
for h in headlines:
    if gemini_yes_no_company(company, ticker, h["title"], h.get("description")):
        relevant.append(h)

# Step 3: Summarize and score sentiment
summary = summarize_and_score(company, ticker, goal, relevant)

# Step 4: Generate Gemini market commentary
today = utc_today().strftime("%B %d, %Y")
prompt = f"Give a detailed opinion about the stock market performance on {today}."
try:
    response = GEMINI.generate_content(prompt)
    commentary = response.text.strip()
except Exception:
    commentary = "Fallback opinion: The market showed mixed signals today."

# Step 5: Analyze sentiment of Gemini commentary
sentiment = analyze_sentiment(commentary)

return {
    "company": company,
    "ticker": ticker,
    "summary": summary,
    "gemini_commentary": commentary,
    "commentary_sentiment": sentiment
}



# ----------------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------------------------

