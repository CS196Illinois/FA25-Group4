import json, re
from typing import List, Dict, Any
from config import GEMINI

def clean_company_and_ticker(user_company: str) -> Dict[str, str]:
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