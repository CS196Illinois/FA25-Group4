import os
import sys, re, json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GEMINI_KEY  = os.getenv("GEMINI_KEY")
POLYGON_KEY = os.getenv("POLYGON_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
NEWS_KEY    = os.getenv("NEWS_KEY")

if not GEMINI_KEY:
    print("ERROR: Please set GEMINI_KEY in your environment or .env"); sys.exit(1)

# Single, strict init
try:
    genai.configure(api_key=GEMINI_KEY)
    GEMINI = genai.GenerativeModel("gemini-2.5-flash")
except Exception:
    print("ERROR: google-generativeai not installed or failed to init. pip install google-generativeai")
    raise


def utc_today():
    return datetime.now(timezone.utc).date()

def ymd(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t

def clean_company_and_ticker(user_company: str) -> Dict[str, str]:
    """
    Strict: use GenAI only. If it fails or returns non-JSON, return original text and empty ticker.
    No backup heuristics or maps.
    """
    prompt = (
        "You are a finance assistant. Clean the user company text, fix spelling, and guess the most likely "
        "primary US stock ticker (if any). If unsure search the web for the ticker. Return ONLY JSON with keys: company, ticker.\n\n"
        f'User text: "{user_company}"\nJSON:'
    )
    comp = user_company.strip()
    tick = ""
    try:
        resp = GEMINI.generate_content(prompt)
        txt = (getattr(resp, "text", "") or "").strip()
        m = re.search(r"\{.*\}", txt, re.S)
        if not m:
            return {"company": comp, "ticker": ""}
        obj = json.loads(m.group(0))
        comp = (obj.get("company") or comp).strip()
        tick = (obj.get("ticker") or "").strip().upper()
        return {"company": comp, "ticker": tick}
    except Exception:
        # Strict: no fallback mapping, no guesses.
        return {"company": comp, "ticker": ""}

def gemini_yes_no_company(company: str, ticker: str, title: str, desc: Optional[str]) -> bool:
    """
    Strict: fail CLOSED. Any GenAI error => return False (do not include).
    """
    p = (
        "Answer YES or NO. Is this headline about the COMPANY {company} (ticker {ticker}), "
        "its business/stock/products/execs/financials—NOT unrelated firms?\n"
        "Headline: {h}\nDescription: {d}\nOnly YES or NO:"
    ).format(company=company, ticker=(ticker or "unknown"), h=(title or "")[:300], d=(desc or "")[:500])
    try:
        r = GEMINI.generate_content(p)
        return "YES" in (r.text or "").strip().upper()
    except Exception:
        return False  # strict: do NOT pass through on error

def summarize_and_score_json(company: str, ticker: str, goal: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Strict: requires valid JSON from GenAI. If invalid, raise ValueError.
    """
    items = []
    for r in rows[:20]:
        items.append({
            "title": (r.get("title") or "")[:300],
            "source": r.get("source") or "",
            "desc": (r.get("description") or "")[:500]
        })
    if not items:
        return {"bullets": [], "long": "No relevant headlines.", "stance":"Neutral", "score":5, "reason":"Insufficient data."}

    prompt = (
        "You are an investment assistant.\n"
        f"Company: {company} ({ticker or 'unknown'})\n"
        f"User goal: {goal}  # short-term=days/weeks; long-term=6+ months\n\n"
        "Recent items (JSON array of {title,source,desc}):\n"
        + json.dumps(items, ensure_ascii=False, indent=2)
        + "\n\nReturn STRICT JSON with keys:\n"
        '{\n'
        '  "bullets": ["...", "..."],            # 4-6 concise investor bullets\n'
        '  "long": "8-12 sentences narrative",   # a single long paragraph is OK\n'
        '  "stance": "Bullish|Neutral|Bearish",\n'
        '  "score": 1-9,\n'
        '  "reason": "one short reason"\n'
        '}\n'
        "No extra text, no markdown, just JSON."
    )
    r = GEMINI.generate_content(prompt)
    txt = (r.text or "").strip()

    m = re.search(r"\{.*\}\s*$", txt, re.S)
    if not m:
        raise ValueError("GenAI summarizer did not return strict JSON.")
    data = json.loads(m.group(0))

    # guard rails (type/shape), but not inventing content
    bullets = list(data.get("bullets") or [])
    longp   = (data.get("long") or "").strip()
    stance  = (data.get("stance") or "Neutral").capitalize()
    try:
        score = int(data.get("score"))
    except Exception:
        raise ValueError("GenAI score missing or not an integer 1-9.")
    reason  = (data.get("reason") or "").strip()

    if stance not in {"Bullish","Neutral","Bearish"}:
        raise ValueError("GenAI stance invalid.")
    if not (1 <= score <= 9):
        raise ValueError("GenAI score out of range 1-9.")
    if not longp:
        raise ValueError("GenAI long summary missing.")
    if len(bullets) == 0:
        raise ValueError("GenAI bullets missing.")

    return {"bullets": bullets[:6], "long": longp, "stance": stance, "score": score, "reason": reason}

def must_be_about(company: str, ticker: str, title: str, desc: Optional[str]) -> bool:
    text = f"{title or ''} {desc or ''}".lower()
    cname = company.lower()
    if cname in text:
        return True
    if ticker and re.search(rf"\b{re.escape(ticker.lower())}\b", text):
        return True
    return False

# ============ PROVIDERS (attach provider ids for dedupe) ============
def fetch_polygon(ticker: str, limit: int = 40) -> pd.DataFrame:
    if not POLYGON_KEY or not ticker: return pd.DataFrame()
    url = "https://api.polygon.io/v2/reference/news"
    r = requests.get(url, params={"ticker": ticker, "limit": min(max(1,limit),100), "apiKey": POLYGON_KEY}, timeout=30)
    r.raise_for_status()
    items = r.json().get("results", []) or []
    if not items: return pd.DataFrame()
    df = pd.DataFrame(items)
    df["date"]  = pd.to_datetime(df.get("published_utc"), errors="coerce", utc=True)
    df["source"]= df.get("publisher").apply(lambda s: (s or {}).get("name") if isinstance(s, dict) else s)
    df["title"] = df.get("title")
    df["url"]   = df.get("article_url")
    df["description"] = df.get("description")
    df["pid"]   = df.get("id", None)
    df["provider"] = "polygon"
    return df[["date","source","title","url","description","pid","provider"]].dropna(subset=["title"]).sort_values("date", ascending=False).reset_index(drop=True)

def fetch_recent_news(company: str, ticker: str, days: int = 5, limit: int = 50) -> pd.DataFrame:
    frames = []
    try:
        p = fetch_polygon(ticker, limit)
        if not p.empty: frames.append(p)
    except Exception as e:
        print(f"[polygon] skipped: {e}")
    try:
        f = fetch_finnhub(ticker, days, limit)
        if not f.empty: frames.append(f)
    except Exception as e:
        print(f"[finnhub] skipped: {e}")
    try:
        n = fetch_newsapi(company, ticker, days, limit)
        if not n.empty: frames.append(n)
    except Exception as e:
        print(f"[newsapi] skipped: {e}")

    if not frames:
        return pd.DataFrame(columns=["date","source","title","url","description","pid","provider"])

    out = pd.concat(frames, ignore_index=True)
    out["title_norm"] = out["title"].apply(norm_title)
    out = out.drop_duplicates(subset=["pid"], keep="first")
    out = out.drop_duplicates(subset=["title_norm","source"], keep="first")
    out = out.drop_duplicates(subset=["url"], keep="first")

    return out.sort_values("date", ascending=False).head(limit).reset_index(drop=True)

def fetch_finnhub(ticker: str, days: int = 5, limit: int = 40) -> pd.DataFrame:
    if not FINNHUB_KEY or not ticker: return pd.DataFrame()
    end = utc_today(); start = end - timedelta(days=max(1,days))
    url = "https://finnhub.io/api/v1/company-news"
    r = requests.get(url, params={"symbol": ticker, "from": ymd(start), "to": ymd(end), "token": FINNHUB_KEY}, timeout=30)
    r.raise_for_status()
    data = r.json() or []
    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df.get("datetime"), unit="s", errors="coerce", utc=True)
    df["source"] = df.get("source")
    df["title"]  = df.get("headline")
    df["url"]    = df.get("url")
    df["description"] = df.get("summary") if "summary" in df.columns else None
    df["pid"]    = df.get("id", None)
    df["provider"] = "finnhub"
    df = df[["date","source","title","url","description","pid","provider"]].dropna(subset=["title"]).sort_values("date", ascending=False)
    return df.head(limit).reset_index(drop=True)

def fetch_newsapi(company: str, ticker: str, days: int = 7, limit: int = 40) -> pd.DataFrame:
    if not NEWS_KEY: return pd.DataFrame()
    end = utc_today(); start = end - timedelta(days=max(1,days))
    q = (
        f'("{company}" OR {ticker} OR "{ticker} stock") AND '
        f'(stock OR shares OR earnings OR revenue OR guidance OR CEO OR product OR forecast OR quarter OR Nasdaq OR "S&P 500") '
        f'-recipe -recipes -soup -pie -vegan -Thanksgiving -cook -cooking'
    ).replace("OR  OR", "OR")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": q, "from": ymd(start), "to": ymd(end), "language": "en", "sortBy": "publishedAt",
        "searchIn": "title,description", "pageSize": min(max(1,limit),100), "page": 1,
        "domains": ",".join(FINANCE_DOMAINS), "apiKey": NEWS_KEY,
    }
    items = []
    while len(items) < limit:
        next_idx = (params["page"] - 1) * params["pageSize"]
        if next_idx >= 100: break
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200: break
        data = r.json(); arts = data.get("articles", []) or []
        if not arts: break
        items.extend(arts)
        if len(items) >= limit or len(items) >= 100: break
        params["page"] += 1
    if not items: return pd.DataFrame()
    df = pd.DataFrame(items)
    df["date"] = pd.to_datetime(df.get("publishedAt"), errors="coerce", utc=True)
    df["source"] = df["source"].apply(lambda s: (s or {}).get("name") if isinstance(s, dict) else s)
    df["title"]  = df.get("title")
    df["url"]    = df.get("url")
    df["description"] = df.get("description")
    df["pid"]    = df["url"]
    df["provider"] = "newsapi"
    return df[["date","source","title","url","description","pid","provider"]].dropna(subset=["title"]).sort_values("date", ascending=False).head(limit).reset_index(drop=True)


def main():
    print("=== Simple Invest News (Strict v2, no backups) ===")
    user_company = input("Enter a company (e.g., Tesla, AAPL, Nvidia): ").strip()
    goal = input("What is your goal? (short-term / long-term): ").strip().lower()
    goal = "short-term" if "short" in goal else "long-term"

    norm = clean_company_and_ticker(user_company)
    company, ticker = norm["company"], norm["ticker"]
    print(f"\nNormalized: Company = {company}" + (f", Ticker = {ticker}" if ticker else ", Ticker = (none)"))

    if not (POLYGON_KEY or FINNHUB_KEY or NEWS_KEY):
        print("ERROR: Set at least one of POLYGON_KEY, FINNHUB_KEY, NEWS_KEY"); return

    # Fetch
    df = fetch_recent_news(company, ticker, days=5, limit=60)

    # HARD pre-filter: must mention company or ticker
    if not df.empty:
        mask = [must_be_about(company, ticker, t, d) for t, d in zip(df["title"], df["description"])]
        df = df[mask].reset_index(drop=True)

    # Gemini YES/NO filter (strict fail-closed)
    if not df.empty:
        keep = []
        for _, row in df.iterrows():
            if gemini_yes_no_company(company, ticker, row["title"], row.get("description")):
                keep.append(row)
        df = pd.DataFrame(keep) if keep else pd.DataFrame(columns=df.columns)

    if df.empty:
        print("\nNo relevant headlines after strict filtering.")
        return

    # Summarize + stance (STRICT JSON)
    rows = df.to_dict(orient="records")
    try:
        result = summarize_and_score_json(company, ticker, goal, rows)
    except Exception as e:
        print(f"\nERROR: Summarizer failed (strict JSON required): {e}")
        return

    # ===== Output =====
    print("\n--- Investor Bullets ---")
    for b in result["bullets"]:
        print(f"- {b}")

    print("\n--- Long Summary ---")
    print(result["long"])

    print("\n--- Invest Sentiment ---")
    print(f"Stance: {result['stance']} | Score: {result['score']} (1=very negative, 9=very positive)")
    if result["reason"]:
        print(f"Reason: {result['reason']}")

    print("\n--- Relevant Headlines (newest) ---")
    show = df[["date","source","title","url"]].copy()
    try: show["date"] = show["date"].dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception: pass
    for _, r in show.head(12).iterrows():
        print(f"[{r['date']}] {r['source']}: {r['title']}\n  {r['url']}")

    print("\n(Disclaimer: Informational only, not investment advice.)")


FINANCE_DOMAINS = [
    "reuters.com","bloomberg.com","ft.com","wsj.com","cnbc.com",
    "marketwatch.com","finance.yahoo.com","seekingalpha.com","investopedia.com",
    "forbes.com","themotleyfool.com","barrons.com","benzinga.com"
]

if __name__ == "__main__":
    main()