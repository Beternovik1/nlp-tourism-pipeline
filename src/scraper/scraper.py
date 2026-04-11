"""Wanderlog scraper with rate limiting and error handling."""

import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when HTTP 429 received (IP blocked)."""
    pass


def fetch_wanderlog(url: str) -> list[dict]:
    """
    Fetch reviews from Wanderlog URL.

    Args:
        url: Wanderlog destination page URL

    Returns:
        List of review dicts matching schema

    Raises:
        RateLimitError: If HTTP 429 received (IP blocked)
    """
    try:
        response = _fetch_with_retry(url)
        time.sleep(6)  # Rate limit: 10 req/min

        if response.status_code == 429:
            logger.warning("IP blocked, wait 60 minutes")
            raise RateLimitError("HTTP 429: IP blocked by Wanderlog")

        if response.status_code in (404, 500):
            logger.error(f"HTTP {response.status_code} for {url}, skipping")
            return []

        response.raise_for_status()

        return _parse_reviews(response.text, url)

    except RateLimitError:
        raise
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return []


def _fetch_with_retry(url: str, timeout: int = 10) -> requests.Response:
    """Fetch URL with one retry on timeout."""
    try:
        return requests.get(url, timeout=timeout)
    except requests.Timeout:
        logger.warning(f"Timeout for {url}, retrying once")
        return requests.get(url, timeout=timeout)


def _parse_reviews(html: str, source_url: str) -> list[dict]:
    """Parse HTML to extract reviews matching schema."""
    soup = BeautifulSoup(html, 'lxml')
    reviews = []

    # Find review containers - adjust selectors based on Wanderlog structure
    review_elements = soup.find_all('div', class_='review-card')

    for element in review_elements:
        review = {
            'destination': _extract_destination(soup),
            'review_text': _extract_text(element, 'review-content'),
            'rating': _extract_rating(element),
            'author': _extract_text(element, 'review-author') or 'Anonymous',
            'date': _extract_date(element),
            'url': source_url
        }
        reviews.append(review)

    return reviews


def _extract_destination(soup: BeautifulSoup) -> str:
    """Extract destination name from page."""
    dest_elem = soup.find('h1', class_='destination-title')
    return dest_elem.get_text(strip=True) if dest_elem else 'Unknown'


def _extract_text(element, class_name: str) -> Optional[str]:
    """Extract text from element by class name."""
    elem = element.find(class_=class_name)
    return elem.get_text(strip=True) if elem else None


def _extract_rating(element) -> Optional[float]:
    """Extract rating as float, return None if missing."""
    rating_elem = element.find(class_='review-rating')
    if not rating_elem:
        return None

    try:
        # Extract numeric value from rating element
        rating_text = rating_elem.get('data-rating') or rating_elem.get_text(strip=True)
        return float(rating_text)
    except (ValueError, AttributeError):
        return None


def _extract_date(element) -> Optional[str]:
    """Extract date in ISO 8601 format."""
    date_elem = element.find(class_='review-date')
    if not date_elem:
        return None

    # Assuming date is in datetime attribute or text
    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
    return date_str if date_str else None
