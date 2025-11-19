"""
Article content fetcher for full-text analysis.

Fetches and extracts full article text from URLs for sentiment analysis.
Uses fail-closed approach: any errors return empty content.
"""
import logging
import time
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Configuration
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
RATE_LIMIT_DELAY = 0.5  # seconds between requests to same domain
MAX_ARTICLE_LENGTH = 15000  # characters (to avoid huge articles)
MIN_ARTICLE_LENGTH = 800  # minimum chars for quality sentiment analysis

# Track last request time per domain for rate limiting
_last_request_time: Dict[str, float] = {}


def extract_article_text(html: str, url: str) -> str:
    """
    Extract main article content from HTML.

    Uses heuristics to identify and extract the main article text,
    filtering out navigation, ads, and other non-content elements.

    Args:
        html: Raw HTML content
        url: Original URL (for logging)

    Returns:
        Extracted article text, or empty string if extraction fails
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, nav, footer, aside elements
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()

        # Try common article containers first
        article_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.article-body',
            '.post-content',
            '.entry-content',
            '#article-body',
            '#main-content',
            '.story-body',
        ]

        article_text = ""

        # Try each selector
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                # Get text from all matching elements
                texts = [elem.get_text(separator=' ', strip=True) for elem in elements]
                article_text = ' '.join(texts)
                if len(article_text) > 200:  # Minimum reasonable article length
                    logger.debug(f"Extracted {len(article_text)} chars using selector '{selector}'")
                    break

        # Fallback: if no article container found, try to get all <p> tags
        if len(article_text) < 200:
            paragraphs = soup.find_all('p')
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            logger.debug(f"Fallback: extracted {len(article_text)} chars from <p> tags")

        # Clean up whitespace
        article_text = ' '.join(article_text.split())

        # Truncate if too long
        if len(article_text) > MAX_ARTICLE_LENGTH:
            article_text = article_text[:MAX_ARTICLE_LENGTH]
            logger.debug(f"Truncated article to {MAX_ARTICLE_LENGTH} chars")

        return article_text

    except Exception as e:
        logger.warning(f"Error extracting article text from {url}: {e}")
        return ""


def fetch_article_content(url: str) -> Optional[str]:
    """
    Fetch and extract full article content from a URL.

    Fail-closed: returns None on any error (network, parsing, paywall, etc.)
    Implements rate limiting per domain.

    Args:
        url: Article URL to fetch

    Returns:
        Extracted article text, or None if fetch/extraction fails
    """
    if not url:
        return None

    try:
        # Parse domain for rate limiting
        parsed = urlparse(url)
        domain = parsed.netloc

        # Rate limiting: wait if we recently hit this domain
        if domain in _last_request_time:
            elapsed = time.time() - _last_request_time[domain]
            if elapsed < RATE_LIMIT_DELAY:
                time.sleep(RATE_LIMIT_DELAY - elapsed)

        # Fetch HTML
        logger.debug(f"Fetching article: {url}")
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )

        _last_request_time[domain] = time.time()

        # Check response
        if response.status_code == 403:
            logger.warning(f"Paywall/forbidden (403): {url}")
            return None

        if response.status_code == 404:
            logger.warning(f"Article not found (404): {url}")
            return None

        response.raise_for_status()

        # Extract article text
        article_text = extract_article_text(response.text, url)

        if not article_text:
            logger.warning(f"Article extraction failed (0 chars): {url}")
            return None

        if len(article_text) < MIN_ARTICLE_LENGTH:
            logger.warning(
                f"Article too short for quality analysis ({len(article_text)} chars, "
                f"min {MIN_ARTICLE_LENGTH}): {url}"
            )
            return None

        logger.info(f"Successfully fetched article ({len(article_text)} chars): {url[:60]}...")
        return article_text

    except requests.Timeout:
        logger.warning(f"Timeout fetching article: {url}")
        return None

    except requests.RequestException as e:
        logger.warning(f"Network error fetching article {url}: {e}")
        return None

    except Exception as e:
        logger.warning(f"Unexpected error fetching article {url}: {e}")
        return None


def fetch_articles_batch(rows: List[Dict]) -> List[Dict]:
    """
    Fetch full article content for a batch of news items.

    Adds 'full_text' field to each row. Sets to None if fetch fails.
    Original rows are not modified - returns new list with added field.

    Args:
        rows: List of news item dicts with 'url' field

    Returns:
        New list of dicts with 'full_text' field added
    """
    if not rows:
        return []

    logger.info(f"Fetching full article content for {len(rows)} articles...")

    enriched_rows = []
    success_count = 0
    failure_reasons = {
        'no_url': 0,
        'failed_fetch': 0,
        'too_short': 0,
    }

    for i, row in enumerate(rows, 1):
        url = row.get('url')

        # Create copy of row
        new_row = row.copy()

        if not url:
            failure_reasons['no_url'] += 1
            logger.warning(f"Article {i}/{len(rows)}: No URL provided")
            new_row['full_text'] = None
            enriched_rows.append(new_row)
            continue

        # Fetch article
        full_text = fetch_article_content(url)
        new_row['full_text'] = full_text

        if full_text:
            success_count += 1
            logger.info(
                f"Article {i}/{len(rows)}: ✓ Fetched ({len(full_text)} chars) - "
                f"{row.get('title', '')[:50]}..."
            )
        else:
            failure_reasons['failed_fetch'] += 1
            logger.warning(
                f"Article {i}/{len(rows)}: ✗ Failed - "
                f"{row.get('title', '')[:50]}..."
            )

        enriched_rows.append(new_row)

    failed_count = len(rows) - success_count
    logger.info(
        f"Article fetching complete: {success_count}/{len(rows)} successful "
        f"({success_count/len(rows)*100:.1f}%), {failed_count} failed"
    )

    if failed_count > 0:
        logger.info(
            f"Failure breakdown: {failure_reasons['no_url']} missing URLs, "
            f"{failure_reasons['failed_fetch']} fetch errors (paywall/timeout/too short)"
        )

    return enriched_rows
