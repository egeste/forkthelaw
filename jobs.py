"""
Job handlers for different types of content scraping.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from scraper import Scraper
from database import Database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobHandler:
    """Base class for job handlers."""

    def __init__(self, scraper: Scraper, database: Database):
        self.scraper = scraper
        self.db = database

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a job. Should be overridden by subclasses.

        Args:
            job: Job dictionary from queue

        Returns:
            Result dictionary with status and data
        """
        raise NotImplementedError


class DiscoverUSCodeTitlesJob(JobHandler):
    """Discovers all US Code titles and creates jobs for each."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Discovering US Code titles...")
        titles = self.scraper.get_us_code_titles()

        created_jobs = 0
        for title_info in titles:
            job_id = self.db.add_job(
                job_type='discover_uscode_sections',
                url=title_info['url'],
                params={'title': title_info['title'], 'name': title_info['name']},
                priority=8
            )
            if job_id:
                created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for US Code titles")
        return {
            'status': 'success',
            'titles_found': len(titles),
            'jobs_created': created_jobs
        }


class DiscoverUSCodeSectionsJob(JobHandler):
    """Discovers all sections within a US Code title."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        title = job['params']['title']
        url = job['url']

        logger.info(f"Discovering sections for US Code Title {title}...")
        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch title page'}

        soup = self.scraper.parse_html(response.text)
        created_jobs = 0

        # Find all section links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match patterns like /uscode/text/1/1, /uscode/text/1/chapter-1, etc.
            if f'/uscode/text/{title}/' in href:
                absolute_url = urljoin(self.scraper.BASE_URL, href)

                # Determine if this is a section or intermediate page
                parts = href.split('/')
                if len(parts) >= 5:  # Has subsections
                    job_type = 'scrape_uscode_section'
                    priority = 5
                else:  # Intermediate level (chapter, subchapter)
                    job_type = 'discover_uscode_sections'
                    priority = 7

                job_id = self.db.add_job(
                    job_type=job_type,
                    url=absolute_url,
                    params={'title': title, 'path': href},
                    priority=priority
                )
                if job_id:
                    created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for Title {title} sections")
        return {
            'status': 'success',
            'title': title,
            'jobs_created': created_jobs
        }


class ScrapeUSCodeSectionJob(JobHandler):
    """Scrapes a specific US Code section."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        title = job['params'].get('title')

        logger.info(f"Scraping US Code section: {url}")
        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch section'}

        soup = self.scraper.parse_html(response.text)

        # Extract section information
        section_title = soup.find('h1') or soup.find('h2')
        section_title_text = section_title.get_text(strip=True) if section_title else "Untitled"

        # Extract main content
        content_div = soup.find('div', class_='content') or soup.find('div', id='content')
        if content_div:
            text_content = self.scraper.extract_text(content_div)
            html_content = str(content_div)
        else:
            text_content = self.scraper.extract_text(soup)
            html_content = str(soup)

        # Parse section number from URL
        path_parts = url.split('/')
        section = path_parts[-1] if path_parts else ""
        chapter = path_parts[-2] if len(path_parts) > 1 else None

        # Save to database
        self.db.save_us_code(
            title=title,
            section=section,
            section_title=section_title_text,
            text_content=text_content,
            html_content=html_content,
            url=url,
            chapter=chapter
        )

        logger.info(f"Saved US Code section: Title {title}, Section {section}")
        return {
            'status': 'success',
            'title': title,
            'section': section
        }


class DiscoverCFRTitlesJob(JobHandler):
    """Discovers all CFR titles and creates jobs for each."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Discovering CFR titles...")
        titles = self.scraper.get_cfr_titles()

        created_jobs = 0
        for title_info in titles:
            job_id = self.db.add_job(
                job_type='discover_cfr_sections',
                url=title_info['url'],
                params={'title': title_info['title'], 'name': title_info['name']},
                priority=8
            )
            if job_id:
                created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for CFR titles")
        return {
            'status': 'success',
            'titles_found': len(titles),
            'jobs_created': created_jobs
        }


class DiscoverCFRSectionsJob(JobHandler):
    """Discovers all sections within a CFR title."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        title = job['params']['title']
        url = job['url']

        logger.info(f"Discovering sections for CFR Title {title}...")
        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch title page'}

        soup = self.scraper.parse_html(response.text)
        created_jobs = 0

        # Find all section links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if f'/cfr/text/{title}/' in href:
                absolute_url = urljoin(self.scraper.BASE_URL, href)

                # Determine depth - deeper URLs are actual sections
                parts = href.rstrip('/').split('/')
                if len(parts) >= 5:  # Actual section
                    job_type = 'scrape_cfr_section'
                    priority = 5
                else:  # Intermediate level
                    job_type = 'discover_cfr_sections'
                    priority = 7

                job_id = self.db.add_job(
                    job_type=job_type,
                    url=absolute_url,
                    params={'title': title, 'path': href},
                    priority=priority
                )
                if job_id:
                    created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for CFR Title {title}")
        return {
            'status': 'success',
            'title': title,
            'jobs_created': created_jobs
        }


class ScrapeCFRSectionJob(JobHandler):
    """Scrapes a specific CFR section."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        title = job['params'].get('title')

        logger.info(f"Scraping CFR section: {url}")
        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch section'}

        soup = self.scraper.parse_html(response.text)

        # Extract section information
        section_title = soup.find('h1') or soup.find('h2')
        section_title_text = section_title.get_text(strip=True) if section_title else "Untitled"

        # Extract main content
        content_div = soup.find('div', class_='content') or soup.find('div', id='content')
        if content_div:
            text_content = self.scraper.extract_text(content_div)
            html_content = str(content_div)
        else:
            text_content = self.scraper.extract_text(soup)
            html_content = str(soup)

        # Parse section info from URL: /cfr/text/{title}/{part}/{section}
        path_parts = url.rstrip('/').split('/')
        section = path_parts[-1] if len(path_parts) >= 5 else ""
        part = path_parts[-2] if len(path_parts) >= 6 else None
        chapter = path_parts[-3] if len(path_parts) >= 7 else None

        # Save to database
        self.db.save_cfr(
            title=title,
            section=section,
            section_title=section_title_text,
            text_content=text_content,
            html_content=html_content,
            url=url,
            chapter=chapter,
            part=part
        )

        logger.info(f"Saved CFR section: Title {title}, Section {section}")
        return {
            'status': 'success',
            'title': title,
            'section': section
        }


class DiscoverSupremeCourtCasesJob(JobHandler):
    """Discovers Supreme Court cases and creates scrape jobs."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        logger.info(f"Discovering Supreme Court cases from: {url}")

        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch cases page'}

        soup = self.scraper.parse_html(response.text)
        created_jobs = 0

        # Find all case links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/supremecourt/text/' in href:
                absolute_url = urljoin(self.scraper.BASE_URL, href)
                job_id = self.db.add_job(
                    job_type='scrape_scotus_case',
                    url=absolute_url,
                    params={},
                    priority=6
                )
                if job_id:
                    created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for Supreme Court cases")
        return {
            'status': 'success',
            'jobs_created': created_jobs
        }


class ScrapeSupremeCourtCaseJob(JobHandler):
    """Scrapes a specific Supreme Court case."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        logger.info(f"Scraping Supreme Court case: {url}")

        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch case'}

        soup = self.scraper.parse_html(response.text)

        # Extract case name
        case_name_elem = soup.find('h1') or soup.find('h2')
        case_name = case_name_elem.get_text(strip=True) if case_name_elem else "Unknown Case"

        # Extract metadata
        metadata = self.scraper.extract_metadata(soup)

        # Try to extract citation and docket number
        citation_pattern = r'\d+\s+U\.S\.?\s+\d+'
        docket_pattern = r'No\.\s*[\d-]+'

        text_content = soup.get_text()
        citation_match = re.search(citation_pattern, text_content)
        docket_match = re.search(docket_pattern, text_content)

        if citation_match:
            metadata['citation'] = citation_match.group()
        if docket_match:
            metadata['docket_number'] = docket_match.group()

        # Extract year from URL or content
        year_match = re.search(r'/(19|20)\d{2}/', url)
        if year_match:
            metadata['year'] = int(year_match.group(1) + year_match.group(2))

        # Extract main content
        content_div = soup.find('div', class_='content') or soup.find('div', id='content')
        if content_div:
            text_content = self.scraper.extract_text(content_div)
            html_content = str(content_div)
        else:
            text_content = self.scraper.extract_text(soup)
            html_content = str(soup)

        # Save to database
        self.db.save_supreme_court_case(
            case_name=case_name,
            url=url,
            text_content=text_content,
            html_content=html_content,
            metadata=metadata
        )

        logger.info(f"Saved Supreme Court case: {case_name}")
        return {
            'status': 'success',
            'case_name': case_name
        }


class DiscoverConstitutionJob(JobHandler):
    """Discovers Constitution articles and amendments."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        logger.info(f"Discovering Constitution sections from: {url}")

        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch Constitution page'}

        soup = self.scraper.parse_html(response.text)
        created_jobs = 0

        # Find all article and amendment links
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Match /constitution/articlei through /constitution/articlevii
            # and /constitution/amendmenti through /constitution/amendmentxxvii
            if '/constitution/article' in href or '/constitution/amendment' in href:
                # Skip the annotated version links
                if 'constitution-conan' in href:
                    continue

                absolute_url = urljoin(self.scraper.BASE_URL, href)

                # Determine if this is an article or amendment
                if '/article' in href:
                    section_type = 'article'
                else:
                    section_type = 'amendment'

                job_id = self.db.add_job(
                    job_type='scrape_constitution_section',
                    url=absolute_url,
                    params={'section_type': section_type},
                    priority=8
                )
                if job_id:
                    created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for Constitution sections")
        return {
            'status': 'success',
            'jobs_created': created_jobs
        }


class ScrapeConstitutionSectionJob(JobHandler):
    """Scrapes a specific Constitution article or amendment."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        section_type = job['params'].get('section_type', 'unknown')

        logger.info(f"Scraping Constitution {section_type}: {url}")

        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch section'}

        soup = self.scraper.parse_html(response.text)

        # Extract title
        title_elem = soup.find('h1') or soup.find('h2')
        title = title_elem.get_text(strip=True) if title_elem else "Untitled"

        # Extract main content
        content_div = soup.find('div', class_='content') or soup.find('div', id='content')
        if content_div:
            text_content = self.scraper.extract_text(content_div)
            html_content = str(content_div)
        else:
            text_content = self.scraper.extract_text(soup)
            html_content = str(soup)

        # Parse article/section from URL: /constitution/articlei or /constitution/amendmenti
        path_parts = url.rstrip('/').split('/')
        section_id = path_parts[-1] if path_parts else ""

        # Determine article or amendment designation
        article = None
        section = None

        if 'article' in section_id.lower():
            article = section_id
        elif 'amendment' in section_id.lower():
            section = section_id

        # Save to database
        self.db.save_constitution(
            article=article,
            section=section,
            title=title,
            text_content=text_content,
            html_content=html_content,
            url=url
        )

        logger.info(f"Saved Constitution section: {title}")
        return {
            'status': 'success',
            'title': title
        }


class DiscoverFederalRulesJob(JobHandler):
    """Discovers Federal Rules sets and creates jobs for each."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Discovering Federal Rules sets...")

        # Known rule sets from LII
        rule_sets = [
            {'code': 'frap', 'name': 'Federal Rules of Appellate Procedure'},
            {'code': 'frcp', 'name': 'Federal Rules of Civil Procedure'},
            {'code': 'frcrmp', 'name': 'Federal Rules of Criminal Procedure'},
            {'code': 'fre', 'name': 'Federal Rules of Evidence'},
            {'code': 'frbp', 'name': 'Federal Rules of Bankruptcy Procedure'},
            {'code': 'supct', 'name': 'Supreme Court Rules'},
        ]

        created_jobs = 0
        for rule_set in rule_sets:
            url = f"{self.scraper.BASE_URL}/rules/{rule_set['code']}"
            job_id = self.db.add_job(
                job_type='discover_federal_rule_sections',
                url=url,
                params={'rule_set': rule_set['code'], 'name': rule_set['name']},
                priority=8
            )
            if job_id:
                created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for Federal Rules sets")
        return {
            'status': 'success',
            'rule_sets_found': len(rule_sets),
            'jobs_created': created_jobs
        }


class DiscoverFederalRuleSectionsJob(JobHandler):
    """Discovers individual rules within a Federal Rules set."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        rule_set = job['params'].get('rule_set')
        rule_name = job['params'].get('name', rule_set)

        logger.info(f"Discovering rules for {rule_name}...")
        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch rules page'}

        soup = self.scraper.parse_html(response.text)
        created_jobs = 0

        # Find all rule links - pattern: /rules/{code}/rule_{number}
        for link in soup.find_all('a', href=True):
            href = link['href']
            if f'/rules/{rule_set}/rule_' in href:
                absolute_url = urljoin(self.scraper.BASE_URL, href)

                # Extract rule number from URL
                rule_match = re.search(r'/rule_([\d.]+)', href)
                rule_number = rule_match.group(1) if rule_match else None

                job_id = self.db.add_job(
                    job_type='scrape_federal_rule',
                    url=absolute_url,
                    params={
                        'rule_set': rule_set,
                        'rule_number': rule_number,
                        'rule_set_name': rule_name
                    },
                    priority=6
                )
                if job_id:
                    created_jobs += 1

        logger.info(f"Created {created_jobs} jobs for {rule_name} rules")
        return {
            'status': 'success',
            'rule_set': rule_set,
            'jobs_created': created_jobs
        }


class ScrapeFederalRuleJob(JobHandler):
    """Scrapes a specific Federal Rule."""

    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        rule_set = job['params'].get('rule_set')
        rule_number = job['params'].get('rule_number')
        rule_set_name = job['params'].get('rule_set_name', rule_set)

        logger.info(f"Scraping {rule_set_name} Rule {rule_number}: {url}")

        response = self.scraper.fetch(url)
        if not response:
            return {'status': 'error', 'error': 'Failed to fetch rule'}

        soup = self.scraper.parse_html(response.text)

        # Extract rule title
        title_elem = soup.find('h1') or soup.find('h2')
        title = title_elem.get_text(strip=True) if title_elem else f"Rule {rule_number}"

        # Extract main content
        content_div = soup.find('div', class_='content') or soup.find('div', id='content')
        if content_div:
            text_content = self.scraper.extract_text(content_div)
            html_content = str(content_div)
        else:
            text_content = self.scraper.extract_text(soup)
            html_content = str(soup)

        # Save to database
        self.db.save_federal_rule(
            rule_set=rule_set,
            rule_number=rule_number,
            title=title,
            text_content=text_content,
            html_content=html_content,
            url=url
        )

        logger.info(f"Saved {rule_set_name} Rule {rule_number}")
        return {
            'status': 'success',
            'rule_set': rule_set,
            'rule_number': rule_number
        }


# Job registry mapping job types to handler classes
JOB_REGISTRY = {
    'discover_uscode_titles': DiscoverUSCodeTitlesJob,
    'discover_uscode_sections': DiscoverUSCodeSectionsJob,
    'scrape_uscode_section': ScrapeUSCodeSectionJob,
    'discover_cfr_titles': DiscoverCFRTitlesJob,
    'discover_cfr_sections': DiscoverCFRSectionsJob,
    'scrape_cfr_section': ScrapeCFRSectionJob,
    'discover_scotus_cases': DiscoverSupremeCourtCasesJob,
    'scrape_scotus_case': ScrapeSupremeCourtCaseJob,
    'discover_constitution': DiscoverConstitutionJob,
    'scrape_constitution_section': ScrapeConstitutionSectionJob,
    'discover_federal_rules': DiscoverFederalRulesJob,
    'discover_federal_rule_sections': DiscoverFederalRuleSectionsJob,
    'scrape_federal_rule': ScrapeFederalRuleJob,
}
