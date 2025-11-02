import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from config import POLYGON_KEY, FINNHUB_KEY, NEWS_KEY, FINANCE_DOMAINS
# If you already split these helpers into utils.py, import them like:
# from utils import utc_today, ymd, norm_title
# Otherwise you can keep these local versions:

def utc_today():
    return datetime.now(timezone.utc).date()

def ymd(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def norm_title(t: str) -> str:
    """lowercase, collapse whitespace. used for dedupe."""
    import re
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def drop_older_than(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """
    Enforce age cutoff (mainly to keep Polygon aligned with Finnhub/NewsAPI).
    We only keep rows where date >= now - days.
    """
    if df.empty or "date" not in df.columns:
        return df
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return df[df["date"] >= cutoff].reset_index(drop=True)


def fetch_polygon(ticker: str, limit: int = 40) -> pd.DataFrame:
    """
    Pull recent ticker-tagged headlines from Polygon.
    Returns normalized columns:
    [date, source, title, url, description, pid, provider]
    """
    if not POLYGON_KEY or not ticker:
        return pd.DataFrame()

    url = "https://api.polygon.io/v2/reference/news"
    params = {
        "ticker": ticker,
        "limit": min(max(1, limit), 100),
        "apiKey": POLYGON_KEY,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    items = r.json().get("results", []) or []
    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    # Normalize
    df["date"] = pd.to_datetime(
        df.get("published_utc"),
        errors="coerce",
        utc=True,
    )
    # polygon gives `publisher` as an object with "name"
    df["source"] = df.get("publisher").apply(
        lambda s: (s or {}).get("name") if isinstance(s, dict) else s
    )
    df["title"] = df.get("title")
    df["url"] = df.get("article_url")
    df["description"] = df.get("description")
    df["pid"] = df.get("id", None)
    df["provider"] = "polygon"

    df = (
        df[["date", "source", "title", "url", "description", "pid", "provider"]]
        .dropna(subset=["title"])
        .sort_values("date", ascending=False)
        .reset_index(drop=True)
    )

    return df


def fetch_finnhub(ticker: str, days: int = 5, limit: int = 40) -> pd.DataFrame:
    """
    Pull company news from Finnhub within a date range [today-days, today].
    Returns normalized columns:
    [date, source, title, url, description, pid, provider]
    """
    if not FINNHUB_KEY or not ticker:
        return pd.DataFrame()

    end = utc_today()
    start = end - timedelta(days=max(1, days))

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker,
        "from": ymd(start),
        "to": ymd(end),
        "token": FINNHUB_KEY,
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json() or []
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(
        df.get("datetime"),
        unit="s",
        errors="coerce",
        utc=True,
    )
    df["source"] = df.get("source")
    df["title"] = df.get("headline")
    df["url"] = df.get("url")
    # Finnhub sometimes includes a short 'summary'
    df["description"] = (
        df.get("summary") if "summary" in df.columns else None
    )
    df["pid"] = df.get("id", None)
    df["provider"] = "finnhub"

    df = (
        df[["date", "source", "title", "url", "description", "pid", "provider"]]
        .dropna(subset=["title"])
        .sort_values("date", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    return df


def fetch_newsapi(company: str, ticker: str, days: int = 7, limit: int = 40) -> pd.DataFrame:
    """
    Use NewsAPI 'everything' endpoint to search finance-y coverage in
    reputable domains for either the company name or ticker.
    Returns normalized columns:
    [date, source, title, url, description, pid, provider]
    """
    if not NEWS_KEY:
        return pd.DataFrame()

    end = utc_today()
    start = end - timedelta(days=max(1, days))

    # Boolean query tuned toward finance/stock news
    q = (
        f'("{company}" OR {ticker} OR "{ticker} stock") AND '
        f'(stock OR shares OR earnings OR revenue OR guidance OR CEO OR product OR forecast '
        f'OR quarter OR Nasdaq OR "S&P 500") '
        f'-recipe -recipes -soup -pie -vegan -Thanksgiving -cook -cooking'
    ).replace("OR  OR", "OR")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": q,
        "from": ymd(start),
        "to": ymd(end),
        "language": "en",
        "sortBy": "publishedAt",
        "searchIn": "title,description",
        "pageSize": min(max(1, limit), 100),
        "page": 1,
        "domains": ",".join(FINANCE_DOMAINS),
        "apiKey": NEWS_KEY,
    }

    items: List[Dict[str, Any]] = []

    # Basic pagination loop until we hit limit or NewsAPI hard cap
    while len(items) < limit:
        next_idx = (params["page"] - 1) * params["pageSize"]
        if next_idx >= 100:
            break

        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            break

        data = r.json()
        arts = data.get("articles", []) or []
        if not arts:
            break

        items.extend(arts)

        if len(items) >= limit or len(items) >= 100:
            break

        params["page"] += 1

    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    df["date"] = pd.to_datetime(
        df.get("publishedAt"),
        errors="coerce",
        utc=True,
    )
    df["source"] = df["source"].apply(
        lambda s: (s or {}).get("name") if isinstance(s, dict) else s
    )
    df["title"] = df.get("title")
    df["url"] = df.get("url")
    df["description"] = df.get("description")
    # We'll treat URL as pid since NewsAPI doesn't give an ID
    df["pid"] = df["url"]
    df["provider"] = "newsapi"

    df = (
        df[["date", "source", "title", "url", "description", "pid", "provider"]]
        .dropna(subset=["title"])
        .sort_values("date", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    return df


def fetch_recent_news(
    company: str,
    ticker: str,
    days: int = 5,
    limit: int = 50
) -> pd.DataFrame:
    """
    High-level function your main script should call.
    - tries Polygon, Finnhub, NewsAPI
    - merges
    - trims by recency
    - dedupes
    - returns newest first

    Output columns:
    [date, source, title, url, description, pid, provider, title_norm]
    """

    frames = []

    # Polygon
    try:
        poly_df = fetch_polygon(ticker, limit)
        if not poly_df.empty:
            frames.append(poly_df)
    except Exception as e:
        print(f"[polygon] skipped: {e}")

    # Finnhub
    try:
        fin_df = fetch_finnhub(ticker, days, limit)
        if not fin_df.empty:
            frames.append(fin_df)
    except Exception as e:
        print(f"[finnhub] skipped: {e}")

    # NewsAPI (doesn't need ticker to strictly exist, uses name too)
    try:
        news_df = fetch_newsapi(company, ticker, days, limit)
        if not news_df.empty:
            frames.append(news_df)
    except Exception as e:
        print(f"[newsapi] skipped: {e}")

    # No data at all?
    if not frames:
        return pd.DataFrame(
            columns=[
                "date",
                "source",
                "title",
                "url",
                "description",
                "pid",
                "provider",
                "title_norm",
            ]
        )

    # Combine all sources
    out = pd.concat(frames, ignore_index=True)

    # Keep only stories within last `days` days (helps rein in Polygon)
    out = drop_older_than(out, days)

    # Add normalized title for dedupe
    out["title_norm"] = out["title"].apply(norm_title)

    # Dedupe:
    # 1. provider's own id
    out = out.drop_duplicates(subset=["pid"], keep="first")
    # 2. same headline from same source
    out = out.drop_duplicates(subset=["title_norm", "source"], keep="first")
    # 3. exact URL
    out = out.drop_duplicates(subset=["url"], keep="first")

    # Sort newest first and cap result count
    out = (
        out.sort_values("date", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    return out
