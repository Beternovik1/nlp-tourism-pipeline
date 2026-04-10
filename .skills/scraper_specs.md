# Scraper Specs: Wanderlog Data Extraction

## 1. Objective
Extract destination reviews, ratings, and metadata from Wanderlog for NLP analysis. Target: 100-500 reviews per destination.

## 2. Tech Stack
- **BeautifulSoup4**: HTML parsing (lxml parser for speed)
- **Requests**: HTTP client (session pooling for efficiency)
- **Rate Limiter**: `time.sleep(6)` between requests (max 10/min per ENGRAM.md warning)

## 3. Target Data Schema
```python
{
    "destination": str,        # e.g., "Tokyo, Japan"
    "review_text": str,        # Full review content
    "rating": float,           # 1.0 - 5.0, or None if missing
    "author": str,             # Username or "Anonymous"
    "date": str,               # ISO 8601 format: "2024-03-15"
    "url": str                 # Source URL for audit trail
}
```
- **Output format**: JSON Lines (`.jsonl`), one record per line
- **File naming**: `data/wanderlog_{destination}_{timestamp}.jsonl`

## 4. Rate Limiting Strategy
**CRITICAL**: Wanderlog blocks IPs after >10 requests/min (per ENGRAM.md)

Implementation:
```python
import time

def fetch_page(url):
    response = requests.get(url)
    time.sleep(6)  # 10 req/min = 6 sec between requests
    return response
```

On HTTP 429:
- Stop scraping immediately
- Log warning: "IP blocked, wait 60 minutes"
- Raise exception (don't silently continue)

## 5. Error Handling
- **HTTP 429**: Stop, log IP block, raise exception
- **HTTP 404/500**: Log error, skip URL, continue to next
- **Missing fields**: Use `None` for rating/author, don't skip record
- **Timeout**: Set `requests.get(timeout=10)`, retry once, then skip

## 6. Testing Requirements
- **Mock all HTTP**: Use `responses` library, NEVER hit real Wanderlog in tests
- **Fixture location**: `tests/fixtures/sample_wanderlog.html`
- **Test cases**:
  - Parse valid HTML → correct fields extracted
  - Missing rating → `None` in output
  - HTTP 429 → raises exception
  - Rate limiting → verify `time.sleep(6)` called

## 7. Entry Point
- **File**: `src/scraper/scraper.py`
- **Function signature**:
```python
def fetch_wanderlog(url: str) -> list[dict]:
    """
    Fetch reviews from Wanderlog URL.
    
    Args:
        url: Wanderlog destination page URL
    
    Returns:
        List of review dicts matching schema in section 3
    
    Raises:
        RateLimitError: If HTTP 429 received (IP blocked)
    """
    pass
```
