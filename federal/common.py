"""
Common HTTP utilities with retry logic and caching support.
"""

import hashlib
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


logger = logging.getLogger(__name__)


class HttpClient:
    """
    HTTP client with retry logic, ETag support, and rate limiting.
    """

    def __init__(self, rate_limiter=None, user_agent: str = "ForkTheLaw/1.0"):
        """
        Initialize HTTP client.

        Args:
            rate_limiter: Optional RateLimiter instance
            user_agent: User-Agent header value
        """
        self.rate_limiter = rate_limiter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })
        self.etag_cache: Dict[str, str] = {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        reraise=True
    )
    def get(self, url: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            check_etag: bool = False) -> Optional[requests.Response]:
        """
        Perform HTTP GET with retries.

        Args:
            url: URL to fetch
            headers: Optional additional headers
            params: Optional query parameters
            check_etag: If True, check ETag and return None if unchanged

        Returns:
            Response object or None if ETag unchanged
        """
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        request_headers = dict(headers) if headers else {}

        # Add If-None-Match header if we have a cached ETag
        if check_etag and url in self.etag_cache:
            request_headers['If-None-Match'] = self.etag_cache[url]

        logger.debug(f"GET {url}")
        response = self.session.get(url, headers=request_headers, params=params, timeout=30)

        # Handle 304 Not Modified
        if response.status_code == 304:
            logger.debug(f"ETag match for {url}, content unchanged")
            return None

        response.raise_for_status()

        # Cache ETag if present
        if 'ETag' in response.headers:
            self.etag_cache[url] = response.headers['ETag']

        return response

    def download(self, url: str, dest_path: Path,
                 headers: Optional[Dict[str, str]] = None,
                 chunk_size: int = 8192) -> Optional[str]:
        """
        Download file and return SHA256 hash.

        Args:
            url: URL to download
            dest_path: Destination file path
            headers: Optional additional headers
            chunk_size: Chunk size for streaming download

        Returns:
            SHA256 hash of downloaded content, or None on error
        """
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()

        logger.info(f"Downloading {url} to {dest_path}")

        try:
            response = self.session.get(url, headers=headers, stream=True, timeout=60)
            response.raise_for_status()

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            sha256 = hashlib.sha256()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        sha256.update(chunk)

            hash_hex = sha256.hexdigest()
            logger.info(f"Downloaded {url} (sha256: {hash_hex[:16]}...)")
            return hash_hex

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            if dest_path.exists():
                dest_path.unlink()
            return None


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
