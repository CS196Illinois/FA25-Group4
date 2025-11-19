"""
Quote extraction pipeline - Second branch of analysis workflow.

After article_fetcher produces articles with full_text, this module extracts
the 10-20 most investment-relevant quotes across all articles and assigns
importance weights (0-1). These quotes will later be used for sentiment analysis.

Pipeline position:
  main.py → article_fetcher.py → [quotes.py] → (future: sentiment analysis)
                                 ↓
                            [summarize.py] (separate branch)
"""

import re
import json
from typing import List, Dict, Any
from utils.config import GEMINI


def extract_quotes_from_articles(articles: List[Dict[str, Any]], company_name: str, num_quotes: int = 15) -> List[Dict[str, Any]]:
    """
    Main entry point: Extract top investment-relevant quotes from all articles.

    This function analyzes all articles together and identifies the most important
    quotes for investment analysis, assigning each a weight from 0 to 1.

    Args:
        articles: List of article dicts from article_fetcher (with 'full_text' field)
        company_name: Company name for context
        num_quotes: Number of top quotes to extract (10-20, default 15)

    Returns:
        List of quote dictionaries sorted by weight (highest first):
        [
            {
                "quote": str,              # The actual quote text
                "speaker": str,            # Who said it (or "Unknown")
                "weight": float,           # Importance weight 0-1
                "context": str,            # Why it matters for investors
                "source_article": {        # Article metadata
                    "title": str,
                    "source": str,
                    "url": str,
                    "date": datetime
                }
            },
            ...
        ]

        Returns empty list on error (fail-closed).
    """
    if not articles:
        return []

    # Validate and clamp num_quotes
    num_quotes = max(10, min(20, num_quotes))

    # Prepare articles for LLM analysis (limit to avoid token overflow)
    article_data = _prepare_articles_for_analysis(articles[:30])

    if not article_data:
        return []

    # Use LLM to extract quotes with weights
    raw_quotes = _llm_extract_quotes(article_data, company_name, num_quotes)

    if not raw_quotes:
        return []

    # Attach article metadata to quotes
    quotes = _attach_metadata(raw_quotes, articles)

    return quotes


def _prepare_articles_for_analysis(articles: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Prepare articles for LLM processing by extracting key fields and truncating text.

    Args:
        articles: Raw article dictionaries

    Returns:
        List of simplified article data with index, title, source, and text sample
    """
    prepared = []

    for i, article in enumerate(articles):
        # Get text content (prefer full_text, fallback to description)
        text = article.get("full_text") or article.get("description") or ""
        title = article.get("title", "")
        source = article.get("source", "Unknown")

        # Skip articles with insufficient content
        if len(text.strip()) < 50:
            continue

        # Take first 2000 chars to keep prompt size manageable
        text_sample = text[:2000]

        prepared.append({
            "index": i,
            "title": title,
            "source": source,
            "text": text_sample
        })

    return prepared


def _llm_extract_quotes(article_data: List[Dict[str, str]], company_name: str, num_quotes: int) -> List[Dict[str, Any]]:
    """
    Use LLM to extract the most important quotes across all articles.

    Args:
        article_data: Prepared article data from _prepare_articles_for_analysis()
        company_name: Company name for context
        num_quotes: Number of quotes to extract

    Returns:
        List of raw quote dictionaries with quote, speaker, weight, context, article_index
    """
    # Build prompt with all articles
    articles_text = ""
    for art in article_data:
        articles_text += f"\n[ARTICLE {art['index']}]\n"
        articles_text += f"Title: {art['title']}\n"
        articles_text += f"Source: {art['source']}\n"
        articles_text += f"Text: {art['text']}\n"
        articles_text += "---\n"

    prompt = f"""You are analyzing {len(article_data)} financial news articles about {company_name}.

{articles_text}

Your task: Extract the {num_quotes} MOST IMPORTANT quotes across ALL articles for investment decision-making.

PRIORITIZE (in order):
1. Earnings guidance, revenue forecasts, financial targets
2. CEO/CFO statements about performance or strategy
3. Analyst price targets, rating changes, strong opinions
4. Major announcements (M&A, products, market expansion)
5. Competitive positioning, market share data
6. Risk factors, regulatory concerns

For each quote, provide:
- quote: The EXACT text from the article (verbatim, in quotes)
- speaker: Name and role/title (e.g., "Tim Cook, CEO" or "Unknown")
- weight: Importance score 0.0 to 1.0
  * 0.9-1.0 = CRITICAL (direct guidance, major strategy shifts, analyst upgrades/downgrades)
  * 0.7-0.8 = HIGH (executive performance commentary, competitive insights)
  * 0.5-0.6 = MODERATE (business updates, product details)
  * 0.3-0.4 = LOW (background, general industry trends)
- context: One sentence (10-20 words) explaining why this matters to investors
- article_index: The [ARTICLE N] number where this quote appears (0-{len(article_data)-1})

Return ONLY valid JSON (no markdown, no extra text):
{{
  "quotes": [
    {{
      "quote": "exact quote text",
      "speaker": "Name and Role",
      "weight": 0.85,
      "context": "brief explanation",
      "article_index": 0
    }}
  ]
}}

Extract exactly {num_quotes} quotes (or fewer if not enough quality quotes exist).
"""

    try:
        # Call Gemini LLM
        response = GEMINI.generate_content(prompt)
        response_text = response.text.strip()

        # Extract JSON (consistent with project pattern)
        match = re.search(r"\{.*\}", response_text, re.S)
        if not match:
            return []

        data = json.loads(match.group(0))

        # Validate structure
        if "quotes" not in data or not isinstance(data["quotes"], list):
            return []

        # Validate and clean each quote
        validated_quotes = []
        for q in data["quotes"]:
            # Check required fields
            required = ["quote", "speaker", "weight", "context", "article_index"]
            if not all(k in q for k in required):
                continue

            # Validate weight range
            try:
                weight = float(q["weight"])
                if weight < 0 or weight > 1:
                    continue
            except (ValueError, TypeError):
                continue

            # Validate article index
            try:
                article_idx = int(q["article_index"])
                if article_idx < 0 or article_idx >= len(article_data):
                    continue
            except (ValueError, TypeError):
                continue

            # Clean and validate quote text
            quote_text = str(q["quote"]).strip()
            if len(quote_text) < 15:  # Skip very short quotes
                continue

            validated_quotes.append({
                "quote": quote_text,
                "speaker": str(q["speaker"]).strip(),
                "weight": round(weight, 2),
                "context": str(q["context"]).strip(),
                "article_index": article_idx
            })

        # Sort by weight (highest first)
        validated_quotes.sort(key=lambda x: x["weight"], reverse=True)

        return validated_quotes

    except Exception:
        # Fail-closed: return empty list on any error
        return []


def _attach_metadata(raw_quotes: List[Dict[str, Any]], original_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attach full article metadata to extracted quotes.

    Args:
        raw_quotes: Quotes with article_index from LLM
        original_articles: Original article dictionaries

    Returns:
        Quotes with full source_article metadata
    """
    quotes_with_metadata = []

    for q in raw_quotes:
        article_idx = q["article_index"]

        # Get original article
        if article_idx >= len(original_articles):
            continue

        article = original_articles[article_idx]

        # Build quote with metadata
        quotes_with_metadata.append({
            "quote": q["quote"],
            "speaker": q["speaker"],
            "weight": q["weight"],
            "context": q["context"],
            "source_article": {
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "date": article.get("date")
            }
        })

    return quotes_with_metadata


# ============================================================================
# Utility functions for displaying/debugging quotes
# ============================================================================

def print_quotes(quotes: List[Dict[str, Any]]) -> None:
    """
    Pretty-print quotes for debugging/display.

    Args:
        quotes: Quote list from extract_quotes_from_articles()
    """
    if not quotes:
        print("No quotes extracted.")
        return

    print(f"\n{'='*80}")
    print(f"EXTRACTED {len(quotes)} TOP QUOTES")
    print(f"{'='*80}\n")

    for i, q in enumerate(quotes, 1):
        # Visual weight indicator
        weight_blocks = int(q["weight"] * 10)
        weight_bar = "█" * weight_blocks + "░" * (10 - weight_blocks)

        print(f"{i}. [{weight_bar}] {q['weight']:.2f}")
        print(f"   \"{q['quote']}\"")
        print(f"   — {q['speaker']}")
        print(f"   Context: {q['context']}")

        # Format article source
        source_info = q['source_article']
        date_str = "unknown date"
        if source_info.get('date'):
            try:
                date_str = source_info['date'].strftime("%Y-%m-%d")
            except:
                date_str = str(source_info['date'])

        print(f"   Source: {source_info.get('source', 'Unknown')} | {date_str}")
        print()


def get_quote_stats(quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about extracted quotes.

    Args:
        quotes: Quote list from extract_quotes_from_articles()

    Returns:
        Dictionary with statistics:
        {
            "total_quotes": int,
            "avg_weight": float,
            "critical_count": int (weight >= 0.9),
            "high_count": int (weight >= 0.7),
            "top_speakers": List[str]  (most frequently quoted)
        }
    """
    if not quotes:
        return {
            "total_quotes": 0,
            "avg_weight": 0.0,
            "critical_count": 0,
            "high_count": 0,
            "top_speakers": []
        }

    # Calculate metrics
    avg_weight = sum(q["weight"] for q in quotes) / len(quotes)
    critical_count = sum(1 for q in quotes if q["weight"] >= 0.9)
    high_count = sum(1 for q in quotes if q["weight"] >= 0.7)

    # Find most quoted speakers
    speaker_counts = {}
    for q in quotes:
        speaker = q["speaker"]
        if speaker != "Unknown":
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1

    top_speakers = sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_speakers = [speaker for speaker, _ in top_speakers]

    return {
        "total_quotes": len(quotes),
        "avg_weight": round(avg_weight, 2),
        "critical_count": critical_count,
        "high_count": high_count,
        "top_speakers": top_speakers
    }


