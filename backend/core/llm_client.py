import logging
from typing import Dict, List, Optional, Any

from utils.config import GEMINI, gemini_generate_with_fallback

logger = logging.getLogger(__name__)

def gemini_yes_no_company(company: str, ticker: str, title: str, desc: Optional[str]) -> bool:
    """
    Strict: fail CLOSED. Any GenAI error => return False (do not include).

    Uses Gemini to determine if a headline is truly about the specified company.

    Args:
        company: Company name
        ticker: Stock ticker symbol
        title: Article title
        desc: Article description (may be None)

    Returns:
        True if headline is about the company, False otherwise (including errors)
    """
    prompt = (
        f"Answer YES or NO. Is this headline about the COMPANY {company} (ticker {ticker or 'unknown'}), "
        "its business/stock/products/execs/financials—NOT unrelated firms?\n"
        f"Headline: {(title or '')[:300]}\n"
        f"Description: {(desc or '')[:500]}\n"
        "Only YES or NO:"
    )

    try:
        resp = gemini_generate_with_fallback(prompt)
        result = "YES" in (resp.text or "").strip().upper()

        if result:
            logger.debug(f"LLM: YES - '{title[:50]}...'")
        else:
            logger.debug(f"LLM: NO - '{title[:50]}...'")

        return result

    except Exception as e:
        # Strict fail-closed: on any error, exclude the headline
        logger.warning(f"LLM error for '{title[:50]}...': {e}")
        return False


def relevance_filter_batch(
    company: str,
    ticker: str,
    rows: List[Dict[str, Any]],
    batch_size: int = 10
) -> List[bool]:
    """
    Batch process headlines through LLM relevance filter.

    Processes headlines in batches to improve performance over sequential calls.
    Each batch is sent to Gemini in a single prompt.

    Args:
        company: Company name
        ticker: Stock ticker symbol
        rows: List of dicts with 'title' and 'description' keys
        batch_size: Number of headlines per batch (default 10)

    Returns:
        List of booleans indicating which headlines passed the filter
    """
    if not rows:
        logger.info("relevance_filter_batch: No rows to process")
        return []

    total = len(rows)
    logger.info(f"Starting LLM relevance filter for {total} headlines (batch_size={batch_size})")

    results = []
    num_batches = (total + batch_size - 1) // batch_size  # Ceiling division

    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total)
        batch = rows[start_idx:end_idx]

        logger.info(f"Processing batch {batch_idx + 1}/{num_batches} ({len(batch)} headlines)")

        # Build batch prompt
        prompt_parts = [
            f"You are filtering news headlines for relevance to {company} (ticker: {ticker or 'unknown'}).\n",
            "For each headline below, answer YES if it's about this company's business/stock/products/execs/financials.\n",
            "Answer NO if it's about unrelated companies or topics.\n",
            "Return ONLY a JSON array of YES/NO values, one per headline.\n\n"
        ]

        for i, row in enumerate(batch, start=1):
            title = (row.get("title") or "")[:300]
            desc = (row.get("description") or "")[:500]
            prompt_parts.append(f"{i}. Title: {title}\n   Description: {desc}\n")

        prompt_parts.append("\nReturn ONLY JSON array like: [\"YES\", \"NO\", \"YES\", ...]")
        prompt = "".join(prompt_parts)

        try:
            resp = gemini_generate_with_fallback(prompt)
            text = (resp.text or "").strip()

            # Try to extract JSON array
            import json
            import re

            # Look for array pattern
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                answers = json.loads(match.group(0))

                # Validate we got the right number of answers
                if len(answers) != len(batch):
                    logger.warning(
                        f"Batch {batch_idx + 1}: Expected {len(batch)} answers, got {len(answers)}. "
                        f"Falling back to sequential processing."
                    )
                    # Fallback to sequential
                    batch_results = [
                        gemini_yes_no_company(company, ticker, r.get("title", ""), r.get("description"))
                        for r in batch
                    ]
                else:
                    # Convert YES/NO to boolean
                    batch_results = ["YES" in str(ans).upper() for ans in answers]
                    yes_count = sum(batch_results)
                    logger.info(f"Batch {batch_idx + 1}: {yes_count}/{len(batch)} headlines passed")

            else:
                logger.warning(
                    f"Batch {batch_idx + 1}: Could not parse JSON response. "
                    f"Falling back to sequential processing."
                )
                # Fallback to sequential
                batch_results = [
                    gemini_yes_no_company(company, ticker, r.get("title", ""), r.get("description"))
                    for r in batch
                ]

            results.extend(batch_results)

        except Exception as e:
            logger.error(f"Batch {batch_idx + 1} failed: {e}. Falling back to sequential processing.")
            # On batch failure, process sequentially (fail-closed for each item)
            batch_results = [
                gemini_yes_no_company(company, ticker, r.get("title", ""), r.get("description"))
                for r in batch
            ]
            results.extend(batch_results)

    total_passed = sum(results)
    logger.info(f"LLM relevance filter complete: {total_passed}/{total} headlines passed")

    return results
