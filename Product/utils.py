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