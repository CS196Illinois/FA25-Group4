import re
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from typing import Union

def utc_today() -> date:
    """Return today's date in UTC timezone."""
    return datetime.now(timezone.utc).date()

def ymd(d: Union[datetime, date]) -> str:
    """Convert datetime or date object to YYYY-MM-DD string."""
    return d.strftime("%Y-%m-%d")

def norm_title(t: str) -> str:
    """Normalize title for deduplication: lowercase and collapse whitespace."""
    t = (t or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t

def drop_older_than(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """
    Filter DataFrame to keep only rows with dates within the last N days.

    Args:
        df: DataFrame with a 'date' column (timezone-aware datetime)
        days: Number of days to look back from now

    Returns:
        Filtered DataFrame with only recent rows
    """
    if df.empty or "date" not in df.columns:
        return df

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Filter rows where date is after cutoff
    mask = df["date"] >= cutoff
    filtered = df[mask].reset_index(drop=True)

    return filtered