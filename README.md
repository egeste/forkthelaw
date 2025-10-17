# Cornell Law Library Archival System

A queue-based web scraper that downloads and archives legal content from [Cornell's Legal Information Institute](https://www.law.cornell.edu/) into a SQLite database.

## 🤖 Automated Crawling with GitHub Actions

This repository includes GitHub Actions workflows that automatically crawl the law library! The database is persisted between runs, allowing you to build a complete archive without running anything locally.

The crawler runs on-demand via manual workflow dispatch. You can configure the duration (up to 180 minutes).

👉 **[See GitHub Actions Setup Guide](GITHUB_ACTIONS.md)** for automated crawling setup.

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

**Dependencies:**
- Python 3.11+
- requests, beautifulsoup4, lxml (for web scraping)
- pydantic (for data validation)
- sqlalchemy (for database schema management)
- orjson (for JSON parsing)
- tenacity (for retry logic)
- tqdm (for progress bars)
- pytest (for testing)

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

# Reset any stuck jobs
python cli.py reset

# Resume processing
python cli.py run --workers 1
```

**Note:** Always run `reset` after stopping to ensure jobs stuck in "processing" state are returned to the queue.

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

**See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for detailed schema documentation including foreign key relationships and views.**

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
- **Database size**: Plan for several GB of storage (current production database: ~19 MB)

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

## Federal Corpus Ingestion

In addition to crawling Cornell LII, this project includes a complete **federal corpus ingestion system** for primary sources. This system fetches structured legal data directly from government APIs and bulk downloads.

### Sources

The federal ingestion system supports:

- **USC (United States Code)**: USLM XML from the Office of the Law Revision Counsel
- **Public Laws**: Enrolled bills and Statutes at Large from GovInfo
- **CFR (Code of Federal Regulations)**: Annual snapshots from GovInfo API
- **eCFR**: Daily point-in-time CFR versions from eCFR API
- **Federal Register**: Rules, notices, and proposed regulations from FR API
- **Bills**: Bill status XML from GPO and metadata from Congress.gov API

### Federal Ingestion Commands

```bash
# Ingest all federal sources (limited for testing)
python cli.py flc ingest all --limit 5

# Ingest specific sources
python cli.py flc ingest usc --limit 5
python cli.py flc ingest public-laws --limit 3
python cli.py flc ingest cfr --title 21 --parts 1300,1308 --limit 10
python cli.py flc ingest ecfr --title 21 --parts 1308 --days 3
python cli.py flc ingest fr --query "21 CFR 1308" --limit 5
python cli.py flc ingest bills --congress 118 --limit 10

# Query point-in-time CFR (reconstructs CFR as of a specific date)
python cli.py flc point-in-time cfr --id cfr:21:1308:12 --date 2021-03-15

# Export relationship graph (edges between statutes, regulations, etc.)
python cli.py flc graph edges --out edges.csv

# Show federal corpus statistics
python cli.py flc stats
```

### Federal Database Schema

The federal ingestion system adds these tables to `law_library.db`:

- `usc_section` - USC sections with canonical IDs, versioning via sha256
- `public_law` - Public Laws with enactment dates and Statutes at Large citations
- `stat_page` - Statutes at Large pages
- `cfr_unit` - CFR sections with effective dates
- `ecfr_version` - Daily eCFR point-in-time snapshots (delta storage)
- `fr_document` - Federal Register documents with metadata
- `bill` - Bills with status and latest actions
- `bill_version` - Bill text snapshots (introduced, engrossed, enrolled, etc.)
- `bill_event` - Bill lifecycle events
- `edge` - Relationships between legal resources (e.g., PL → USC, CFR → USC)
- `ingestion_state` - Tracks last successful run per source

### Canonical Identifiers

All federal resources use normalized IDs:

- USC: `usc:21:841` (title:section)
- Public Law: `pl:117-328` (congress-number)
- Statutes: `stat:136:4459` (volume:page)
- CFR: `cfr:21:1308:12` (title:part:section)
- Federal Register: `fr:2023-12345` (year-document_number)
- Bill: `bill:118:h:1234` (congress:chamber:number)

### Citation Extraction

The system includes regex-based citation extraction:

```python
from federal.citations import extract_all_citations

text = "See 21 U.S.C. § 841 and 21 CFR § 1308.12, enacted by Pub. L. No. 91-513."
citations = extract_all_citations(text)

# Returns:
# {
#   'usc': [{'usc_id': 'usc:21:841', ...}],
#   'cfr': [{'cfr_id': 'cfr:21:1308:12', ...}],
#   'public_laws': [{'pl_id': 'pl:91-513', ...}],
#   ...
# }
```

### Graph Edges

The system creates edges linking related resources:

- `pl -> usc_section` (adds|amends|repeals) - Public Laws that modify USC
- `usc_section -> cfr_unit` (authority_for) - USC provisions authorizing CFR sections
- `fr_document -> cfr_unit` (amends|proposes) - FR rules modifying CFR
- `bill -> public_law` (enacted_as) - Bills that became Public Laws

Export edges to CSV:
```bash
python cli.py flc graph edges --out edges.csv
```

### Point-in-Time CFR Queries

Reconstruct CFR text as of any date by combining:
1. Annual baseline from GovInfo
2. Daily deltas from eCFR API

```bash
python cli.py flc point-in-time cfr --id cfr:21:1308:12 --date 2021-03-15
```

*(Note: Point-in-time queries return placeholder data in the current implementation; delta reconstruction logic needs to be completed.)*

### Storage

By default, raw downloads are stored in `./federal_data/` (configurable via `LocalStorage`). The storage layer is designed to be swappable with S3 for cloud deployments.

### Testing

Run smoke tests:
```bash
# Unit tests
pytest tests/test_identifiers.py -v
pytest tests/test_citations.py -v
pytest tests/test_ingest_smoke.py -v

# Full workflow test (creates test_law_library.db)
bash test_workflow.sh
```

**Note:** The workflow test creates a temporary database (`test_law_library.db`) for testing purposes.

### Architecture

Federal ingestion uses a modular ETL pipeline:

1. **Discover**: Find available resources (titles, parts, dates)
2. **Fetch**: Download XML/JSON to local storage
3. **Parse**: Extract structured data using lxml/orjson
4. **Upsert**: Insert or update database using natural keys + sha256 versioning

Each ingestor (`federal/*.py`) implements these four functions, plus a `run_pipeline()` entry point.

### Current Status

**Working:**
- Database schema with foreign key constraints ([DATABASE_SCHEMA.md](DATABASE_SCHEMA.md))
- Schema migration script ([migrate_add_foreign_keys.py](migrate_add_foreign_keys.py:1))
- Identifier parsing and citation extraction
- CLI commands (`flc` subcommands)
- Storage abstraction (local file system, swappable with S3)
- Unit tests ([tests/](tests/))
- Smoke test workflow ([test_workflow.sh](test_workflow.sh:1))

**Placeholder/TODO:**
- Actual XML/JSON parsing (currently returns placeholder data)
- Network fetching from GovInfo, eCFR, FR, Congress.gov APIs
- Point-in-time CFR delta reconstruction logic
- Edge generation from parsed citations
- Full integration with worker.py job queue

The skeleton is complete and runnable for testing. Next steps: implement parsers and API clients for each federal source.

## Additional Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes with automated or manual crawling
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Complete database schema with foreign keys and relationships
- **[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)** - GitHub Actions automation setup guide
- **[test_workflow.sh](test_workflow.sh)** - Smoke test script for federal corpus ingestion

## Support

For issues with:
- **This tool**: Check logs and job_results table for errors
- **Cornell's website**: Visit https://www.law.cornell.edu/
- **Legal questions**: Consult a licensed attorney
