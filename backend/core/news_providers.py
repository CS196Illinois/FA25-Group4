import logging
import requests
import pandas as pd
from datetime import timedelta
from typing import List, Dict, Any

from utils.config import POLYGON_KEY, FINNHUB_KEY, NEWS_KEY, FINANCE_DOMAINS
from utils.utils import utc_today, ymd, norm_title, drop_older_than

logger = logging.getLogger(__name__)


def fetch_polygon(ticker: str, limit: int = 40) -> pd.DataFrame:
    """
    Pull recent ticker-tagged headlines from Polygon.
    Returns columns:
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

    df["date"] = pd.to_datetime(
        df.get("published_utc"),
        errors="coerce",
        utc=True,
    )
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
    Pull company news from Finnhub in window [today-days, today].
    Returns columns:
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
    Use NewsAPI 'everything' to search finance-y coverage in known finance domains.
    Returns columns:
    [date, source, title, url, description, pid, provider]
    """
    if not NEWS_KEY:
        return pd.DataFrame()

    end = utc_today()
    start = end - timedelta(days=max(1, days))

    # boolean query leaning hard toward market/financial coverage
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

    # paginate until we've got enough or hit ~100 articles
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
    df["pid"] = df["url"]  # no id from NewsAPI; URL acts as stable id
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
    High-level orchestrator:
    - calls Polygon, Finnhub, NewsAPI
    - enforces recency
    - dedupes
    - sorts newest first
    Returns DataFrame with:
    [date, source, title, url, description, pid, provider, title_norm]
    """

    frames = []
    providers_succeeded = []
    providers_failed = []

    # Polygon
    try:
        logger.info(f"Fetching from Polygon.io (ticker={ticker})")
        poly_df = fetch_polygon(ticker, limit)
        if not poly_df.empty:
            frames.append(poly_df)
            providers_succeeded.append(f"Polygon ({len(poly_df)} articles)")
            logger.info(f"Polygon: Retrieved {len(poly_df)} articles")
        else:
            logger.info("Polygon: No articles returned")
    except Exception as e:
        providers_failed.append(f"Polygon: {e}")
        logger.warning(f"Polygon failed: {e}")

    # Finnhub
    try:
        logger.info(f"Fetching from Finnhub (ticker={ticker}, days={days})")
        fin_df = fetch_finnhub(ticker, days, limit)
        if not fin_df.empty:
            frames.append(fin_df)
            providers_succeeded.append(f"Finnhub ({len(fin_df)} articles)")
            logger.info(f"Finnhub: Retrieved {len(fin_df)} articles")
        else:
            logger.info("Finnhub: No articles returned")
    except Exception as e:
        providers_failed.append(f"Finnhub: {e}")
        logger.warning(f"Finnhub failed: {e}")

    # NewsAPI
    try:
        logger.info(f"Fetching from NewsAPI (company={company}, days={days})")
        news_df = fetch_newsapi(company, ticker, days, limit)
        if not news_df.empty:
            frames.append(news_df)
            providers_succeeded.append(f"NewsAPI ({len(news_df)} articles)")
            logger.info(f"NewsAPI: Retrieved {len(news_df)} articles")
        else:
            logger.info("NewsAPI: No articles returned")
    except Exception as e:
        providers_failed.append(f"NewsAPI: {e}")
        logger.warning(f"NewsAPI failed: {e}")

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

    out = pd.concat(frames, ignore_index=True)

    # align Polygon freshness with the same `days` window
    out = drop_older_than(out, days)

    out["title_norm"] = out["title"].apply(norm_title)

    # Deduplicate
    # 1. provider's own ID
    out = out.drop_duplicates(subset=["pid"], keep="first")
    # 2. same (normalized title + source)
    out = out.drop_duplicates(subset=["title_norm", "source"], keep="first")
    # 3. same URL
    out = out.drop_duplicates(subset=["url"], keep="first")

    out = (
        out.sort_values("date", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )

    logger.info(
        f"Fetch complete: {len(out)} articles after deduplication and filtering. "
        f"Providers succeeded: {len(providers_succeeded)}, failed: {len(providers_failed)}"
    )

    return out