
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