import re
from datetime import datetime, timedelta, timezone

def utc_today():
    return datetime.now(timezone.utc).date()

def ymd(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")

def norm_title(t: str) -> str:
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t

from datetime import datetime, timedelta, timezone

def drop_older_than(df, days: int):
    """
    Drop rows in a DataFrame older than N days based on 'date' column.
    Ensures tz-aware comparison.
    """
    # tz-aware cutoff in UTC
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Ensure df["date"] is tz-aware in UTC
    if df["date"].dt.tz is None:
        df = df.copy()
        df["date"] = df["date"].dt.tz_localize("UTC")

    return df[df["date"] >= cutoff]


