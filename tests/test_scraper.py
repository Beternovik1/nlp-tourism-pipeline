"""Unit tests for Wanderlog scraper."""

import time
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
import requests

from src.scraper.scraper import fetch_wanderlog, RateLimitError


FIXTURES_DIR = Path(__file__).parent / 'fixtures'
TEST_URL = 'https://wanderlog.com/destinations/tokyo-japan'


@pytest.fixture
def sample_html():
    """Load sample Wanderlog HTML fixture."""
    fixture_path = FIXTURES_DIR / 'sample_wanderlog.html'
    return fixture_path.read_text()


@responses.activate
def test_parse_valid_html(sample_html):
    """Parse valid HTML extracts correct fields."""
    responses.add(responses.GET, TEST_URL, body=sample_html, status=200)

    with patch('time.sleep'):  # Skip sleep in tests
        reviews = fetch_wanderlog(TEST_URL)

    assert len(reviews) == 3

    # First review with all fields
    assert reviews[0]['destination'] == 'Tokyo, Japan'
    assert reviews[0]['author'] == 'John Traveler'
    assert reviews[0]['rating'] == 4.5
    assert 'Amazing city' in reviews[0]['review_text']
    assert reviews[0]['date'] == '2024-03-15'
    assert reviews[0]['url'] == TEST_URL

    # Second review
    assert reviews[1]['rating'] == 5.0
    assert reviews[1]['author'] == 'Jane Explorer'


@responses.activate
def test_missing_rating_returns_none(sample_html):
    """Missing rating field returns None in output."""
    responses.add(responses.GET, TEST_URL, body=sample_html, status=200)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    # Third review has no rating
    assert reviews[2]['rating'] is None
    assert reviews[2]['review_text'] == 'Great experience overall. Public transport is excellent.'


@responses.activate
def test_missing_author_defaults_to_anonymous(sample_html):
    """Missing author field defaults to 'Anonymous'."""
    responses.add(responses.GET, TEST_URL, body=sample_html, status=200)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    # Third review has no author
    assert reviews[2]['author'] == 'Anonymous'


@responses.activate
def test_http_429_raises_rate_limit_error():
    """HTTP 429 raises RateLimitError exception."""
    responses.add(responses.GET, TEST_URL, status=429)

    with patch('time.sleep'):
        with pytest.raises(RateLimitError, match='HTTP 429: IP blocked'):
            fetch_wanderlog(TEST_URL)


@responses.activate
def test_http_404_returns_empty_list():
    """HTTP 404 logs error and returns empty list."""
    responses.add(responses.GET, TEST_URL, status=404)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    assert reviews == []


@responses.activate
def test_http_500_returns_empty_list():
    """HTTP 500 logs error and returns empty list."""
    responses.add(responses.GET, TEST_URL, status=500)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    assert reviews == []


@responses.activate
def test_rate_limiting_sleep_called(sample_html):
    """Verify time.sleep(6) is called for rate limiting."""
    responses.add(responses.GET, TEST_URL, body=sample_html, status=200)

    with patch('time.sleep') as mock_sleep:
        fetch_wanderlog(TEST_URL)
        mock_sleep.assert_called_once_with(6)


@responses.activate
def test_timeout_retries_once():
    """Timeout triggers one retry before failing."""
    # First call times out, second succeeds
    responses.add(responses.GET, TEST_URL, body=requests.Timeout())
    responses.add(responses.GET, TEST_URL, body='<html></html>', status=200)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    # Should complete after retry
    assert isinstance(reviews, list)


@responses.activate
def test_empty_html_returns_empty_list():
    """Empty HTML returns empty reviews list."""
    responses.add(responses.GET, TEST_URL, body='<html><body></body></html>', status=200)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    assert reviews == []


@responses.activate
def test_malformed_rating_returns_none():
    """Malformed rating data returns None."""
    html = """
    <html>
        <h1 class="destination-title">Paris, France</h1>
        <div class="review-card">
            <div class="review-author">Test User</div>
            <div class="review-rating">invalid</div>
            <div class="review-content">Test review</div>
        </div>
    </html>
    """
    responses.add(responses.GET, TEST_URL, body=html, status=200)

    with patch('time.sleep'):
        reviews = fetch_wanderlog(TEST_URL)

    assert len(reviews) == 1
    assert reviews[0]['rating'] is None
