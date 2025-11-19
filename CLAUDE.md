# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an investment news aggregation and sentiment analysis tool that:
1. Accepts a company name from the user
2. Resolves the company to its stock ticker using Google Gemini AI
3. Fetches recent news from multiple financial data providers (Polygon.io, Finnhub, NewsAPI)
4. Filters headlines for relevance using LLM-based verification
5. **Fetches full article content** for deeper analysis (bypassing paywalls where possible)
6. Generates an investment sentiment summary (Bullish/Neutral/Bearish) with a 1-9 score based on full article text

## Running the Application

```bash
# Run the main CLI application
python Product/main.py
```

The application will prompt for:
- Company name (e.g., "Apple", "Microsoft", "TSLA")
- Investment goal: "short-term" (days/weeks) or "long-term" (6+ months)

## Environment Setup

Required API keys must be set in a `.env` file in the root directory:
- `GEMINI_KEY` (required) - Google Gemini API for LLM operations
- `POLYGON_KEY` (optional) - Polygon.io for ticker-tagged financial news
- `FINNHUB_KEY` (optional) - Finnhub for company news
- `NEWS_KEY` (optional) - NewsAPI for broad financial coverage

The application will fail if `GEMINI_KEY` is missing. Other keys are optional but reduce data coverage if absent.

## Architecture

### Data Flow Pipeline

The application follows a strict linear pipeline:

1. **Entity Resolution** ([cleaner.py](Product/cleaner.py))
   - Normalizes user input to official company name
   - Resolves primary U.S. stock ticker using Gemini LLM
   - Fail-closed: returns original input if LLM fails

2. **News Aggregation** ([news_providers.py](Product/news_providers.py))
   - Fetches from 3 providers in parallel (Polygon, Finnhub, NewsAPI)
   - Normalizes all sources to common schema: `[date, source, title, url, description, pid, provider, title_norm]`
   - Deduplicates by provider ID, normalized title+source, and URL
   - Enforces recency cutoff (default 5 days)

3. **LLM Relevance Filter** ([llm_client.py](Product/llm_client.py))
   - Strict fail-closed approach: any LLM error → exclude headline
   - Uses Gemini to answer YES/NO: "Is this headline about the company's business/stock/products/execs/financials?"
   - Examines both title and description (up to 500 chars)
   - Processes in batches (default 10) via `relevance_filter_batch()`
   - Individual article check in `gemini_yes_no_company()`

4. **Full Article Fetching** ([article_fetcher.py](Product/article_fetcher.py))
   - NEW: Fetches complete article content from URLs
   - Uses BeautifulSoup for HTML parsing with smart content extraction
   - Implements rate limiting (0.5s per domain) to avoid overwhelming servers
   - Fail-closed: returns None on paywalls, 403/404, timeouts, or parsing errors
   - Extracts up to 15,000 chars of main article content
   - Processes articles via `fetch_articles_batch()`

5. **Summarization & Sentiment** ([summarize.py](Product/summarize.py))
   - Takes top 20 filtered articles with full content
   - Uses first 3,000 chars of full article text (falls back to description if unavailable)
   - Generates 4-6 bullet points, 8-12 sentence narrative
   - Returns structured sentiment: `{bullets, long, stance, score, reason}`
   - Stance: Bullish/Neutral/Bearish
   - Score: 1-9 (1=very negative, 9=very positive)
   - Strict validation: raises ValueError if response format is invalid

### Key Design Principles

- **Fail-Closed Philosophy**: All LLM operations default to conservative behavior on errors (exclude content rather than risk including irrelevant data)
- **Provider Independence**: Each news provider can fail independently without breaking the pipeline
- **Deduplication**: Multi-stage deduplication (by ID, by title+source, by URL) prevents duplicate content
- **Strict JSON Validation**: LLM responses must match exact JSON schemas or the pipeline fails explicitly

### Module Responsibilities

- [config.py](Product/config.py): Centralizes API configuration, initializes Gemini model (`gemini-2.5-pro`), defines trusted finance domains
- [utils.py](Product/utils.py): Date/time utilities (`utc_today`, `ymd`, `norm_title`)
- [cleaner.py](Product/cleaner.py): Company name normalization and ticker resolution
- [news_providers.py](Product/news_providers.py): Multi-source news fetching with `fetch_recent_news()` as the main entry point
- [llm_client.py](Product/llm_client.py): Gemini-based relevance verification (batch processing)
- [article_fetcher.py](Product/article_fetcher.py): Full article content extraction with HTML parsing and rate limiting
- [summarize.py](Product/summarize.py): Investment summary generation with sentiment scoring (uses full article text)
- [main.py](Product/main.py): CLI orchestration in `run_cli()`

## Working with LLM Operations

All Gemini LLM calls use strict JSON parsing with regex extraction:
```python
m = re.search(r"\{.*\}", response_text, re.S)
data = json.loads(m.group(0))
```

When modifying LLM prompts:
- Always specify "Return ONLY JSON" or "Return ONLY strict JSON"
- Include explicit schema in the prompt
- Validate all required fields exist in the response
- Use fail-closed error handling (return conservative defaults on exceptions)

## Data Schema

News items follow this normalized schema after aggregation:
```python
{
    "date": datetime (UTC timezone-aware),
    "source": str (publisher name),
    "title": str,
    "url": str,
    "description": str (may be None for some providers),
    "pid": str (provider-specific ID or URL),
    "provider": str ("polygon" | "finnhub" | "newsapi"),
    "title_norm": str (lowercase, whitespace-collapsed for deduplication),
    "full_text": str | None (complete article content, added after filtering)
}
```

Note: The `full_text` field is added by `article_fetcher.py` after LLM filtering and before sentiment analysis.

## Testing

Manual test files exist in [Product/tests/](Product/tests/):

**Core Component Tests:**
- [test_cleaner_manual.py](Product/tests/test_cleaner_manual.py): Tests company name cleaning and ticker resolution
- [test_validation.py](Product/tests/test_validation.py): Tests enhanced ticker validation system
- [test_article_fetcher.py](Product/tests/test_article_fetcher.py): Tests full article content fetching and HTML parsing
- [test_filtering_debug.py](Product/tests/test_filtering_debug.py): Debug script to analyze LLM filtering decisions

**Provider-Specific Tests:**
- [test_finnhub_api.py](Product/tests/test_finnhub_api.py): Finnhub API integration tests
- [test_finnhub_redirect.py](Product/tests/test_finnhub_redirect.py): Tests for handling Finnhub URL redirects
- [test_finnhub_urls.py](Product/tests/test_finnhub_urls.py): Finnhub URL validation tests

**Edge Case Tests:**
- [test_live_extraction.py](Product/tests/test_live_extraction.py): Tests article extraction with live URLs
- [test_publisher_extraction.py](Product/tests/test_publisher_extraction.py): Tests publisher name extraction
- [test_low_count_article.py](Product/tests/test_low_count_article.py): Tests handling of low article count scenarios