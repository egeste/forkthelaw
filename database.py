"""
Database schema and management for Cornell Law Library archival system.
"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager


class Database:
    """Manages SQLite database operations for law library archival."""

    def __init__(self, db_path: str = "law_library.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Job queue table - tracks pending work
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    params_json TEXT,
                    priority INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    last_attempt_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    UNIQUE(job_type, url)
                )
            """)

            # Job results table - tracks completed/failed jobs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES job_queue(id)
                )
            """)

            # Main documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT,
                    url TEXT UNIQUE NOT NULL,
                    html_content TEXT,
                    text_content TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata_json TEXT
                )
            """)

            # US Code table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS us_code (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title INTEGER NOT NULL,
                    chapter TEXT,
                    section TEXT,
                    section_title TEXT,
                    text_content TEXT,
                    html_content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # CFR table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cfr (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title INTEGER NOT NULL,
                    chapter TEXT,
                    part TEXT,
                    section TEXT,
                    section_title TEXT,
                    text_content TEXT,
                    html_content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Supreme Court cases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS supreme_court_cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_name TEXT NOT NULL,
                    citation TEXT,
                    docket_number TEXT,
                    decision_date DATE,
                    argued_date DATE,
                    year INTEGER,
                    text_content TEXT,
                    html_content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    metadata_json TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Constitution table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS constitution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article TEXT,
                    section TEXT,
                    title TEXT,
                    text_content TEXT,
                    html_content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Federal rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS federal_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_set TEXT NOT NULL,
                    rule_number TEXT,
                    title TEXT,
                    text_content TEXT,
                    html_content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Crawl statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    stat_type TEXT NOT NULL,
                    stat_value TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_queue_status
                ON job_queue(status, priority DESC, created_at)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_queue_type
                ON job_queue(job_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_category
                ON documents(category)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_us_code_title
                ON us_code(title)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cfr_title
                ON cfr(title)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_scotus_year
                ON supreme_court_cases(year)
            """)

            # Enable full-text search on text content
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                USING fts5(title, text_content, content=documents, content_rowid=id)
            """)

            print(f"Database initialized at {self.db_path}")

    def add_job(self, job_type: str, url: str, params: Optional[Dict[str, Any]] = None,
                priority: int = 5) -> Optional[int]:
        """Add a job to the queue. Returns job_id or None if duplicate."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO job_queue (job_type, url, params_json, priority)
                    VALUES (?, ?, ?, ?)
                """, (job_type, url, json.dumps(params) if params else None, priority))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Job already exists
                return None

    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get the next pending job from the queue."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, job_type, url, params_json, attempts
                FROM job_queue
                WHERE status = 'pending' AND attempts < 3
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                job_id = row[0]
                # Mark as processing
                cursor.execute("""
                    UPDATE job_queue
                    SET status = 'processing', last_attempt_at = CURRENT_TIMESTAMP,
                        attempts = attempts + 1
                    WHERE id = ?
                """, (job_id,))
                return {
                    'id': row[0],
                    'job_type': row[1],
                    'url': row[2],
                    'params': json.loads(row[3]) if row[3] else {},
                    'attempts': row[4]
                }
            return None

    def complete_job(self, job_id: int, status: str, result: Optional[Dict[str, Any]] = None,
                     error: Optional[str] = None):
        """Mark a job as completed or failed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Update job status
            final_status = 'completed' if status == 'success' else 'failed'
            cursor.execute("""
                UPDATE job_queue
                SET status = ?
                WHERE id = ?
            """, (final_status, job_id))

            # Record result
            cursor.execute("""
                INSERT INTO job_results (job_id, status, result_json, error)
                VALUES (?, ?, ?, ?)
            """, (job_id, status, json.dumps(result) if result else None, error))

    def retry_job(self, job_id: int):
        """Reset a job to pending status for retry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE job_queue
                SET status = 'pending'
                WHERE id = ?
            """, (job_id,))

    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the job queue."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM job_queue
                GROUP BY status
            """)
            stats = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) FROM job_results WHERE status = 'success'")
            stats['completed'] = cursor.fetchone()[0]

            return stats

    def save_us_code(self, title: int, section: str, section_title: str,
                     text_content: str, html_content: str, url: str,
                     chapter: Optional[str] = None):
        """Save US Code section to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO us_code
                (title, chapter, section, section_title, text_content, html_content, url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, chapter, section, section_title, text_content, html_content, url))

    def save_cfr(self, title: int, section: str, section_title: str,
                 text_content: str, html_content: str, url: str,
                 chapter: Optional[str] = None, part: Optional[str] = None):
        """Save CFR section to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cfr
                (title, chapter, part, section, section_title, text_content, html_content, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, chapter, part, section, section_title, text_content, html_content, url))

    def save_supreme_court_case(self, case_name: str, url: str, text_content: str,
                                html_content: str, metadata: Optional[Dict[str, Any]] = None):
        """Save Supreme Court case to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO supreme_court_cases
                (case_name, citation, docket_number, decision_date, year,
                 text_content, html_content, url, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_name,
                metadata.get('citation') if metadata else None,
                metadata.get('docket_number') if metadata else None,
                metadata.get('decision_date') if metadata else None,
                metadata.get('year') if metadata else None,
                text_content,
                html_content,
                url,
                json.dumps(metadata) if metadata else None
            ))

    def save_document(self, category: str, title: str, url: str,
                     text_content: str, html_content: str,
                     metadata: Optional[Dict[str, Any]] = None):
        """Save a generic document to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents
                (category, title, url, text_content, html_content, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (category, title, url, text_content, html_content,
                  json.dumps(metadata) if metadata else None))

    def save_constitution(self, article: Optional[str], section: Optional[str],
                         title: str, text_content: str, html_content: str, url: str):
        """Save Constitution section to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO constitution
                (article, section, title, text_content, html_content, url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (article, section, title, text_content, html_content, url))

    def save_federal_rule(self, rule_set: str, rule_number: Optional[str],
                         title: str, text_content: str, html_content: str, url: str):
        """Save Federal Rule to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO federal_rules
                (rule_set, rule_number, title, text_content, html_content, url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule_set, rule_number, title, text_content, html_content, url))
