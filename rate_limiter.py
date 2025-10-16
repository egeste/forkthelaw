"""
Rate limiter for respecting robots.txt crawl delay.
"""

import time
import threading
from collections import defaultdict
from typing import Dict


class RateLimiter:
    """Thread-safe rate limiter that enforces delays between requests."""

    def __init__(self, delay_seconds: float = 10.0):
        """
        Initialize rate limiter.

        Args:
            delay_seconds: Minimum seconds between requests (default 10 per robots.txt)
        """
        self.delay_seconds = delay_seconds
        self.last_request_time: Dict[str, float] = defaultdict(float)
        self.lock = threading.Lock()

    def wait_if_needed(self, domain: str = "law.cornell.edu"):
        """
        Wait if necessary to respect rate limit for the given domain.

        Args:
            domain: Domain to rate limit (default: law.cornell.edu)
        """
        with self.lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time[domain]

            if time_since_last_request < self.delay_seconds:
                sleep_time = self.delay_seconds - time_since_last_request
                print(f"Rate limiting: waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

            self.last_request_time[domain] = time.time()

    def reset(self, domain: str = "law.cornell.edu"):
        """Reset the rate limiter for a domain."""
        with self.lock:
            if domain in self.last_request_time:
                del self.last_request_time[domain]


class TokenBucketRateLimiter:
    """
    Alternative token bucket rate limiter for more flexible rate limiting.
    Allows burst requests up to a limit, then enforces steady rate.
    """

    def __init__(self, rate: float = 0.1, capacity: int = 1):
        """
        Initialize token bucket rate limiter.

        Args:
            rate: Tokens per second (0.1 = one request per 10 seconds)
            capacity: Maximum number of tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def wait_for_token(self):
        """Wait until a token is available, then consume it."""
        with self.lock:
            while True:
                current_time = time.time()
                elapsed = current_time - self.last_update
                self.last_update = current_time

                # Add tokens based on elapsed time
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.rate
                time.sleep(wait_time)
