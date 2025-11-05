import json
import re
from typing import List, Dict, Any

from config import GEMINI


def summarize_and_score(
    company: str,
    ticker: str,
    goal: str,
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:

    items = []
    for r in rows[:20]:
        items.append({
            "title": (r.get("title") or "")[:300],
            "source": r.get("source") or "",
            "desc": (r.get("description") or "")[:500]
        })

    if not items:
        return {
            "bullets": [],
            "long": "No relevant headlines.",
            "stance": "Neutral",
            "score": 5,
            "reason": "Insufficient data."
        }

    prompt = (
        "You are an investment assistant.\n"
        f"Company: {company} ({ticker or 'unknown'})\n"
        f"User goal: {goal}  # short-term=days/weeks; long-term=6+ months\n\n"
        "Recent items (JSON array of {title,source,desc}):\n"
        + json.dumps(items, ensure_ascii=False, indent=2)
        + "\n\nReturn STRICT JSON with keys:\n"
        '{\n'
        '  "bullets": ["...", "..."],            # 4-6 concise investor bullets\n'
        '  "long": "8-12 sentences narrative",   # one long paragraph allowed\n'
        '  "stance": "Bullish|Neutral|Bearish",\n'
        '  "score": 1-9,\n'
        '  "reason": "one short reason"\n'
        '}\n'
        "No extra text, no markdown, just JSON."
    )

    resp = GEMINI.generate_content(prompt)
    txt = (getattr(resp, "text", "") or "").strip()

    m = re.search(r"\{.*\}\s*$", txt, re.S)
    if not m:
        raise ValueError("Summarizer did not return strict JSON.")

    data = json.loads(m.group(0))

    bullets = list(data.get("bullets") or [])
    longp   = (data.get("long") or "").strip()
    stance  = (data.get("stance") or "Neutral").capitalize()

    try:
        score = int(data.get("score"))
    except Exception:
        raise ValueError("Summarizer score missing or not an integer 1-9.")

    reason  = (data.get("reason") or "").strip()

    if stance not in {"Bullish","Neutral","Bearish"}:
        raise ValueError("Summarizer stance invalid.")
    if not (1 <= score <= 9):
        raise ValueError("Summarizer score out of range 1-9.")
    if not longp:
        raise ValueError("Summarizer long summary missing.")
    if len(bullets) == 0:
        raise ValueError("Summarizer bullets missing.")

    return {
        "bullets": bullets[:6],
        "long": longp,
        "stance": stance,
        "score": score,
        "reason": reason
    }