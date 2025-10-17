# Database Schema Documentation

## Overview

This database uses SQLite with foreign key constraints enabled to maintain referential integrity. The schema is organized into two main sections:

1. **Cornell Law Scraper Tables** - For archiving legal documents from Cornell LII
2. **Federal Corpus Tables** - For comprehensive federal legal data

## Foreign Key Constraints

### Enforced Foreign Keys

The following tables have explicit foreign key constraints:

| Child Table | Column | Parent Table | Parent Column | Description |
|------------|--------|--------------|---------------|-------------|
| `job_results` | `job_id` | `job_queue` | `id` | Links job results to their queue entries |
| `bill_version` | `bill_id` | `bill` | `bill_id` | Links bill versions to bills |
| `bill_event` | `bill_id` | `bill` | `bill_id` | Links bill events to bills |

### Natural Key Relationships

The following tables use natural keys (text-based identifiers) that reference other tables but don't use SQL foreign keys:

| Table | Natural Key | References | Notes |
|-------|-------------|------------|-------|
| `ecfr_version` | `cfr_id` | `cfr_unit.cfr_id` | Can't use FK because cfr_id is not unique in cfr_unit (has multiple effective dates) |
| `edge` | `src_id`, `dst_id` | Various tables | Polymorphic relationship - can reference multiple table types |

## Cornell Law Scraper Tables

### Job Management

#### `job_queue`
Tracks scraping jobs to be processed.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `(job_type, url)`
- **Indexed**: `status`, `priority`, `created_at`, `job_type`

#### `job_results`
Records the outcome of completed jobs.
- **Primary Key**: `id` (INTEGER)
- **Foreign Key**: `job_id` → `job_queue.id`

### Document Storage

#### `documents`
Generic document storage for archived legal materials.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`
- **Indexed**: `category`
- **Full-Text Search**: Title and text content indexed via `documents_fts`

#### `us_code`
US Code sections from Cornell LII.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`
- **Indexed**: `title`

#### `cfr`
Code of Federal Regulations sections from Cornell LII.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`
- **Indexed**: `title`

#### `supreme_court_cases`
Supreme Court cases from Cornell LII.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`
- **Indexed**: `year`

#### `constitution`
US Constitution articles and amendments.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`

#### `federal_rules`
Federal Rules (Civil Procedure, Criminal Procedure, Evidence, etc.).
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `url`

### Statistics

#### `crawl_stats`
Historical statistics about crawling operations.
- **Primary Key**: `id` (INTEGER)
- No foreign keys (aggregate data)

## Federal Corpus Tables

### US Code (USC)

#### `usc_section`
US Code sections with full text and metadata.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `usc_id`
- **Indexed**: `title`, `(title, section)`, `sha256`
- **View**: `v_usc_latest` - Shows only the most recent version of each section

### Public Laws & Statutes

#### `public_law`
Enacted public laws.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `pl_id`
- **Indexed**: `congress`, `enactment_date`

#### `stat_page`
Statutes at Large pages.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `stat_id`
- **Indexed**: `(volume, page)`

### Code of Federal Regulations (CFR)

#### `cfr_unit`
CFR sections with versioning by effective date.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `(cfr_id, effective_date)`
- **Indexed**: `(title, part)`, `effective_date`, `cfr_id`
- **Views**:
  - `v_cfr_latest` - Most recent version of each CFR unit
  - `v_cfr_baseline` - GovInfo baseline versions

#### `ecfr_version`
Daily point-in-time snapshots of eCFR with delta tracking.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `(cfr_id, version_date)`
- **Natural Key Reference**: `cfr_id` references `cfr_unit.cfr_id`
- **Indexed**: `(cfr_id, version_date)`

### Federal Register

#### `fr_document`
Federal Register documents (rules, notices, etc.).
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `fr_id`
- **Indexed**: `publication_date`, `agency`, `doc_type`

### Bills & Legislation

#### `bill`
Congressional bills with metadata.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `bill_id`
- **Indexed**: `congress`, `(congress, chamber)`
- **View**: `v_bill_summary` - Bills with their latest version info

#### `bill_version`
Versions of bill text (introduced, engrossed, enrolled, etc.).
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `(bill_id, version_code)`
- **Foreign Key**: `bill_id` → `bill.bill_id`
- **Indexed**: `bill_id`

#### `bill_event`
Timeline of bill actions (votes, committee actions, etc.).
- **Primary Key**: `id` (INTEGER)
- **Foreign Key**: `bill_id` → `bill.bill_id`
- **Indexed**: `(bill_id, event_time)`

### Relationships

#### `edge`
Polymorphic relationship graph linking legal documents.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `(src_id, dst_id, rel_type)`
- **Indexed**: `(src_id, src_type)`, `(dst_id, dst_type)`, `rel_type`
- **View**: `v_edge_stats` - Aggregated relationship statistics

Examples of relationships:
- USC section → Public Law (codifies)
- Bill → USC section (amends)
- CFR rule → USC section (implements)
- Federal Register document → CFR section (proposes/amends)

### System Tables

#### `ingestion_state`
Tracks ingestion progress for different data sources.
- **Primary Key**: `id` (INTEGER)
- **Unique Constraint**: `source`
- **Indexed**: `source`
- **View**: `v_ingestion_health` - Health monitoring of data sources

## Foreign Key Enforcement

Foreign keys are enabled globally via:
```python
conn.execute("PRAGMA foreign_keys = ON")
```

This is set in:
1. `Database.get_connection()` - For all database operations
2. `Database.init_database()` - During schema initialization

## Migration

To enable foreign keys on an existing database:
```bash
python migrate_add_foreign_keys.py
```

This script:
1. Enables foreign key enforcement
2. Verifies no violations exist
3. Confirms all constraints are active

## Data Integrity

### Cascading Actions

Current foreign keys use the default `NO ACTION` behavior:
- Deleting a parent record will fail if children exist
- This prevents accidental data loss

### Natural Keys vs. Surrogate Keys

The schema uses a mix:
- **Surrogate keys** (auto-increment INTEGER): For simple parent-child relationships
- **Natural keys** (TEXT): For cross-system references (e.g., bill_id, usc_id, cfr_id)

Natural keys are preferred when:
- The ID has external meaning
- The ID is stable across systems
- The ID appears in multiple tables

## Query Examples

### Find all results for completed jobs
```sql
SELECT jq.url, jr.status, jr.completed_at
FROM job_queue jq
JOIN job_results jr ON jr.job_id = jq.id
WHERE jq.status = 'completed';
```

### Get all versions of a bill
```sql
SELECT b.bill_id, b.title, bv.version_code, bv.date
FROM bill b
JOIN bill_version bv ON bv.bill_id = b.bill_id
WHERE b.bill_id = 'hr1234-118'
ORDER BY bv.date;
```

### Find CFR sections amended by a Federal Register document
```sql
SELECT c.cfr_id, c.heading, e.rel_type, f.title as fr_title
FROM cfr_unit c
JOIN edge e ON e.dst_id = c.cfr_id AND e.dst_type = 'cfr'
JOIN fr_document f ON f.fr_id = e.src_id AND e.src_type = 'fr'
WHERE e.rel_type IN ('amends', 'proposes_amendment');
```

### Track ingestion health
```sql
SELECT source, last_success, days_since_success, status
FROM v_ingestion_health
WHERE status != 'healthy';
```
