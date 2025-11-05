import json
import re
import logging
from typing import List, Dict, Any

from config import GEMINI

logger = logging.getLogger(__name__)


def summarize_and_score(
    company: str,
    ticker: str,
    goal: str,
    rows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate investment summary and sentiment for a company based on news articles.

    Args:
        company: Company name
        ticker: Stock ticker symbol
        goal: Investment timeframe ("short-term" or "long-term")
        rows: List of news article dicts with 'title', 'source', 'description'
              Optional: 'full_text' field with complete article content (preferred)

    Returns:
        Dict with keys: bullets, long, stance, score, reason
    """

    items = []
    for r in rows[:20]:
        # Use full article text if available, otherwise fall back to description
        full_text = r.get("full_text")
        if full_text and len(full_text) > 100:
            # Use first 3000 chars of full article for better context
            content = full_text[:3000]
        else:
            # Fall back to short description
            content = (r.get("description") or "")[:500]

        items.append({
            "title": (r.get("title") or "")[:300],
            "source": r.get("source") or "",
            "content": content  # Can be full article excerpt or description
        })

    if not items:
        logger.warning(f"No headlines provided for summarization of {company}")
        return {
            "bullets": [],
            "long": "No relevant headlines.",
            "stance": "Neutral",
            "score": 5,
            "reason": "Insufficient data."
        }

    logger.info(f"Generating summary for {company} based on {len(items)} headlines (goal: {goal})")

    prompt = (
        "You are an investment assistant.\n"
        f"Company: {company} ({ticker or 'unknown'})\n"
        f"User goal: {goal}  # short-term=days/weeks; long-term=6+ months\n\n"
        "Recent items (JSON array of {title,source,content}):\n"
        "Note: 'content' may include full article text or just a summary.\n"
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

    try:
        resp = GEMINI.generate_content(prompt)
        txt = (getattr(resp, "text", "") or "").strip()

        m = re.search(r"\{.*\}\s*$", txt, re.S)
        if not m:
            logger.error("Summarizer did not return strict JSON")
            raise ValueError("Summarizer did not return strict JSON.")

        data = json.loads(m.group(0))

        bullets = list(data.get("bullets") or [])
        longp = (data.get("long") or "").strip()
        stance = (data.get("stance") or "Neutral").capitalize()

        try:
            score = int(data.get("score"))
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid score in summary response: {data.get('score')}")
            raise ValueError("Summarizer score missing or not an integer 1-9.")

        reason = (data.get("reason") or "").strip()

        # Validation
        if stance not in {"Bullish", "Neutral", "Bearish"}:
            logger.error(f"Invalid stance: {stance}")
            raise ValueError(f"Summarizer stance invalid: {stance}")

        if not (1 <= score <= 9):
            logger.error(f"Score out of range: {score}")
            raise ValueError(f"Summarizer score out of range 1-9: {score}")

        if not longp:
            logger.error("Long summary missing from response")
            raise ValueError("Summarizer long summary missing.")

        if len(bullets) == 0:
            logger.error("Bullets missing from response")
            raise ValueError("Summarizer bullets missing.")

        logger.info(
            f"Summary generated: stance={stance}, score={score}, "
            f"{len(bullets)} bullets, {len(longp)} char summary"
        )

        return {
            "bullets": bullets[:6],
            "long": longp,
            "stance": stance,
            "score": score,
            "reason": reason
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in summarizer: {e}")
        raise ValueError(f"Summarizer returned invalid JSON: {e}")

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        raise