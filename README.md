# Cornell Law Library Archival System

A queue-based web scraper that downloads and archives legal content from [Cornell's Legal Information Institute](https://www.law.cornell.edu/) into a SQLite database.

## 🤖 Automated Crawling with GitHub Actions

**NEW:** This repository includes GitHub Actions workflows that automatically crawl the law library for 3 hours daily! The database is persisted between runs, allowing you to build a complete archive without running anything locally.

👉 **[See GitHub Actions Setup Guide](GITHUB_ACTIONS.md)** for automated daily crawling.

## Features

- **Queue-based architecture** - Resilient, resumable downloads
- **Rate limiting** - Respects robots.txt (10-second delay between requests)
- **Multi-threaded workers** - Configurable worker pool
- **Automatic retry** - Failed jobs retry up to 3 times
- **Comprehensive coverage** - US Code, CFR, Supreme Court cases, Constitution, Federal Rules
- **Full-text search** - SQLite FTS5 indexes for fast searching
- **Progress tracking** - Real-time statistics and logging

## Architecture

The system uses a job queue pattern where:

1. **Discovery jobs** scan index pages and create specific scraping jobs
2. **Scraping jobs** download individual documents
3. **Workers** pull jobs from the queue and process them
4. **Database** stores both the queue state and archived content

This architecture allows:
- Stopping and resuming at any time
- Graceful handling of errors and rate limits
- Easy scaling by adding more workers
- Complete audit trail of what was downloaded

## Installation

```bash
# Clone or download the project
cd forkthelaw

# Install dependencies
pip install -r requirements.txt
```

## Usage

### 1. Initialize and Seed the Queue

Seed the job queue with discovery jobs for the content you want to archive:

```bash
# Seed all content types
python cli.py seed --all

# Or seed specific content types
python cli.py seed --uscode --cfr --scotus
```

Available content types:
- `--uscode` - US Code (federal statutes)
- `--cfr` - Code of Federal Regulations
- `--scotus` - Supreme Court cases
- `--constitution` - US Constitution (articles and amendments)
- `--federal_rules` - Federal Rules (civil, criminal, evidence, bankruptcy, appellate, Supreme Court)
- `--all` - All of the above

### 2. Run the Workers

Start the worker pool to begin downloading:

```bash
# Run with 1 worker (recommended to respect rate limits)
python cli.py run --workers 1

# Run with 2 workers (still within rate limits)
python cli.py run --workers 2

# Custom delay between requests (default 10 seconds)
python cli.py run --workers 1 --delay 15.0
```

The workers will:
- Process jobs from the queue
- Respect the 10-second rate limit
- Automatically retry failed jobs
- Report statistics every minute
- Continue until all jobs are complete

### 3. Monitor Progress

```bash
# View statistics
python cli.py stats
```

Output shows:
- Job queue status (pending, processing, completed, failed)
- Documents archived by type
- Total documents downloaded

### 4. Resume After Stopping

The system is designed to be stopped and resumed:

```bash
# Stop with Ctrl+C (graceful shutdown)

# Reset any stuck jobs (optional)
python cli.py reset

# Resume processing
python cli.py run --workers 1
```

## Database Schema

The system creates `law_library.db` with the following tables:

### Content Tables
- `us_code` - US Code sections with title, chapter, section
- `cfr` - CFR sections with title, part, section
- `supreme_court_cases` - SCOTUS cases with metadata
- `constitution` - Constitutional provisions
- `federal_rules` - Federal rules of procedure
- `documents` - Generic documents

### Queue Tables
- `job_queue` - Pending and in-progress jobs
- `job_results` - Completed and failed job results
- `crawl_stats` - Aggregate statistics

### Full-Text Search
- `documents_fts` - FTS5 virtual table for fast text search

## Querying the Database

```python
import sqlite3

# Connect to database
conn = sqlite3.connect('law_library.db')
cursor = conn.cursor()

# Search US Code
cursor.execute("""
    SELECT title, section, section_title, text_content
    FROM us_code
    WHERE text_content LIKE '%freedom of speech%'
    LIMIT 10
""")

# Get all CFR sections for a specific title
cursor.execute("""
    SELECT section_title, url
    FROM cfr
    WHERE title = 21
    ORDER BY section
""")

# Full-text search across all documents
cursor.execute("""
    SELECT title, snippet(documents_fts, 1, '<b>', '</b>', '...', 32)
    FROM documents_fts
    WHERE documents_fts MATCH 'privacy'
    LIMIT 20
""")
```

## Configuration

Key configuration options in the code:

- **Rate limit**: 10 seconds (in `rate_limiter.py`)
- **Max retries**: 3 attempts per job (in `database.py`)
- **Request timeout**: 30 seconds (in `scraper.py`)
- **Stats interval**: 60 seconds (in `worker.py`)

## Job Types

The system uses these job types:

1. `discover_uscode_titles` - Find all US Code titles
2. `discover_uscode_sections` - Find sections within a title
3. `scrape_uscode_section` - Download a specific section
4. `discover_cfr_titles` - Find all CFR titles
5. `discover_cfr_sections` - Find sections within a CFR title
6. `scrape_cfr_section` - Download a CFR section
7. `discover_scotus_cases` - Find Supreme Court cases
8. `scrape_scotus_case` - Download a specific case
9. `discover_constitution` - Find Constitution articles and amendments
10. `scrape_constitution_section` - Download a specific article or amendment
11. `discover_federal_rules` - Find Federal Rules sets
12. `discover_federal_rule_sections` - Find individual rules within a set
13. `scrape_federal_rule` - Download a specific rule

## Extending

To add new content types:

1. Add job handler class in `jobs.py`
2. Register in `JOB_REGISTRY`
3. Add database save method in `database.py`
4. Add seed logic in `cli.py`

Example job handler:

```python
class ScrapeNewContentJob(JobHandler):
    def handle(self, job: Dict[str, Any]) -> Dict[str, Any]:
        url = job['url']
        response = self.scraper.fetch(url)

        if not response:
            return {'status': 'error', 'error': 'Failed to fetch'}

        soup = self.scraper.parse_html(response.text)
        # ... extract and save content ...

        return {'status': 'success'}
```

## Performance Considerations

- **Download time**: With 10-second delays, expect ~6 requests/minute per worker
- **US Code**: ~54,000+ sections (estimated 90+ hours with 1 worker)
- **CFR**: ~200,000+ sections (estimated 333+ hours with 1 worker)
- **Database size**: Plan for several GB of storage

Using 2 workers can approximately halve these times while staying within rate limits.

## Ethical Considerations

This tool is designed for:
- Educational and research purposes
- Creating personal legal reference libraries
- Archival and backup purposes

Please:
- Respect the 10-second crawl delay
- Don't run excessive concurrent workers
- Use archived data responsibly
- Check Cornell LII's terms of service

## License

This is an educational project. The legal content belongs to the US Government (public domain) and is provided by Cornell's Legal Information Institute.

## Troubleshooting

### Jobs stuck in "processing" state

```bash
python cli.py reset
```

### Database locked errors

- Reduce number of workers
- Ensure only one worker pool is running

### Rate limit errors (HTTP 429)

- System automatically backs off
- Consider increasing delay: `--delay 15.0`

### Out of memory

- Process one content type at a time
- The database handles large datasets efficiently

## Support

For issues with:
- **This tool**: Check logs and job_results table for errors
- **Cornell's website**: Visit https://www.law.cornell.edu/
- **Legal questions**: Consult a licensed attorney
