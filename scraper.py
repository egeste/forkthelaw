"""
Base scraper class with HTTP requests and retry logic.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import time
from urllib.parse import urljoin, urlparse
import logging

from rate_limiter import RateLimiter


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Scraper:
    """Base scraper class for fetching and parsing web content."""

    BASE_URL = "https://www.law.cornell.edu"

    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize scraper.

        Args:
            rate_limiter: RateLimiter instance (creates default if not provided)
        """
        self.rate_limiter = rate_limiter or RateLimiter(delay_seconds=10.0)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LawLibraryArchiver/1.0 (Educational archival project)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def fetch(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Fetch a URL with rate limiting and retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Response object or None if all retries failed
        """
        if not url.startswith('http'):
            url = urljoin(self.BASE_URL, url)

        for attempt in range(max_retries):
            try:
                # Respect rate limit
                self.rate_limiter.wait_if_needed()

                logger.info(f"Fetching: {url} (attempt {attempt + 1}/{max_retries})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"404 Not Found: {url}")
                    return None
                elif e.response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {url}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep((attempt + 1) * 5)

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching {url}")
                if attempt == max_retries - 1:
                    return None
                time.sleep((attempt + 1) * 5)

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep((attempt + 1) * 10)

            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep((attempt + 1) * 5)

        return None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content into BeautifulSoup object.

        Args:
            html_content: Raw HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')

    def extract_text(self, soup: BeautifulSoup, selector: Optional[str] = None) -> str:
        """
        Extract clean text from HTML.

        Args:
            soup: BeautifulSoup object
            selector: Optional CSS selector to limit extraction

        Returns:
            Cleaned text content
        """
        if selector:
            element = soup.select_one(selector)
            if not element:
                return ""
            soup = element

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # Get text and clean it up
        text = soup.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        return '\n'.join(lines)

    def extract_links(self, soup: BeautifulSoup, base_url: str,
                     filter_prefix: Optional[str] = None) -> List[str]:
        """
        Extract all links from a page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            filter_prefix: Only include links starting with this prefix

        Returns:
            List of absolute URLs
        """
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            if filter_prefix and not absolute_url.startswith(filter_prefix):
                continue

            # Remove fragments
            parsed = urlparse(absolute_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"

            if clean_url not in links:
                links.append(clean_url)

        return links

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract metadata from page (title, description, etc.).

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Page title
        title_tag = soup.find('title')
        if title_tag:
            metadata['page_title'] = title_tag.get_text(strip=True)

        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content']

        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = keywords_tag['content']

        # Publication date
        date_tag = soup.find('meta', attrs={'property': 'article:published_time'})
        if date_tag and date_tag.get('content'):
            metadata['published_date'] = date_tag['content']

        return metadata

    def get_us_code_titles(self) -> List[Dict[str, Any]]:
        """
        Get list of all US Code titles.

        Returns:
            List of dictionaries with title number and name
        """
        url = f"{self.BASE_URL}/uscode/text"
        response = self.fetch(url)
        if not response:
            return []

        soup = self.parse_html(response.text)
        titles = []

        # Find all title links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/uscode/text/' in href and href.count('/') == 3:
                try:
                    title_num = int(href.split('/')[-1])
                    title_name = link.get_text(strip=True)
                    titles.append({
                        'title': title_num,
                        'name': title_name,
                        'url': urljoin(self.BASE_URL, href)
                    })
                except ValueError:
                    continue

        return titles

    def get_cfr_titles(self) -> List[Dict[str, Any]]:
        """
        Get list of all CFR titles.

        Returns:
            List of dictionaries with title number and name
        """
        url = f"{self.BASE_URL}/cfr/text"
        response = self.fetch(url)
        if not response:
            return []

        soup = self.parse_html(response.text)
        titles = []

        # Find all title links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/cfr/text/' in href and href.count('/') == 3:
                try:
                    title_num = int(href.split('/')[-1])
                    title_name = link.get_text(strip=True)
                    titles.append({
                        'title': title_num,
                        'name': title_name,
                        'url': urljoin(self.BASE_URL, href)
                    })
                except ValueError:
                    continue

        return titles
