#!/usr/bin/env python3
"""
Command-line interface for Cornell Law Library archival system.
"""

import argparse
import sys
import logging
from pathlib import Path

from database import Database
from worker import WorkerPool
from rate_limiter import RateLimiter


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_jobs(db: Database, content_types: list):
    """
    Seed the job queue with initial discovery jobs.

    Args:
        db: Database instance
        content_types: List of content types to seed
    """
    jobs_created = 0

    if 'uscode' in content_types or 'all' in content_types:
        logger.info("Seeding US Code discovery job...")
        job_id = db.add_job(
            job_type='discover_uscode_titles',
            url='https://www.law.cornell.edu/uscode/text',
            priority=10
        )
        if job_id:
            jobs_created += 1
            logger.info("Created US Code discovery job")

    if 'cfr' in content_types or 'all' in content_types:
        logger.info("Seeding CFR discovery job...")
        job_id = db.add_job(
            job_type='discover_cfr_titles',
            url='https://www.law.cornell.edu/cfr/text',
            priority=10
        )
        if job_id:
            jobs_created += 1
            logger.info("Created CFR discovery job")

    if 'scotus' in content_types or 'all' in content_types:
        logger.info("Seeding Supreme Court discovery jobs...")
        # Seed jobs for different browsing methods
        urls = [
            'https://www.law.cornell.edu/supremecourt/text/topic',
            'https://www.law.cornell.edu/supremecourt/text/author',
            'https://www.law.cornell.edu/supremecourt/text/party',
        ]
        for url in urls:
            job_id = db.add_job(
                job_type='discover_scotus_cases',
                url=url,
                priority=9
            )
            if job_id:
                jobs_created += 1

        logger.info("Created Supreme Court discovery jobs")

    if 'constitution' in content_types or 'all' in content_types:
        logger.info("Seeding Constitution discovery job...")
        job_id = db.add_job(
            job_type='discover_constitution',
            url='https://www.law.cornell.edu/constitution',
            priority=10
        )
        if job_id:
            jobs_created += 1
            logger.info("Created Constitution discovery job")

    if 'federal_rules' in content_types or 'all' in content_types:
        logger.info("Seeding Federal Rules discovery job...")
        job_id = db.add_job(
            job_type='discover_federal_rules',
            url='https://www.law.cornell.edu/rules',
            priority=10
        )
        if job_id:
            jobs_created += 1
            logger.info("Created Federal Rules discovery job")

    logger.info(f"Total seed jobs created: {jobs_created}")
    return jobs_created


def show_stats(db: Database):
    """Show statistics about the database and queue."""
    stats = db.get_queue_stats()

    print("\n" + "=" * 60)
    print("CORNELL LAW LIBRARY ARCHIVAL - STATISTICS")
    print("=" * 60)
    print("\nJob Queue Status:")
    print(f"  Pending:    {stats.get('pending', 0):,}")
    print(f"  Processing: {stats.get('processing', 0):,}")
    print(f"  Completed:  {stats.get('completed', 0):,}")
    print(f"  Failed:     {stats.get('failed', 0):,}")

    # Count documents in database
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM us_code")
        uscode_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cfr")
        cfr_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM supreme_court_cases")
        scotus_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM constitution")
        constitution_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM federal_rules")
        federal_rules_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents")
        docs_count = cursor.fetchone()[0]

    print("\nDocuments Archived:")
    print(f"  US Code Sections:      {uscode_count:,}")
    print(f"  CFR Sections:          {cfr_count:,}")
    print(f"  Supreme Court Cases:   {scotus_count:,}")
    print(f"  Constitution:          {constitution_count:,}")
    print(f"  Federal Rules:         {federal_rules_count:,}")
    print(f"  Other Documents:       {docs_count:,}")
    total_count = uscode_count + cfr_count + scotus_count + constitution_count + federal_rules_count + docs_count
    print(f"  Total:                 {total_count:,}")
    print("=" * 60 + "\n")


def reset_stuck_jobs(db: Database):
    """Reset jobs that are stuck in 'processing' state."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE job_queue
            SET status = 'pending', last_attempt_at = NULL
            WHERE status = 'processing'
        """)
        count = cursor.rowcount
        logger.info(f"Reset {count} stuck jobs to pending status")
    return count


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Cornell Law Library Archival System - Queue-based web scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize and seed all content types
  %(prog)s seed --all

  # Seed specific content types
  %(prog)s seed --uscode --cfr

  # Start workers
  %(prog)s run --workers 2

  # Show statistics
  %(prog)s stats

  # Reset stuck jobs
  %(prog)s reset
        """
    )

    parser.add_argument(
        '--db',
        default='law_library.db',
        help='Path to SQLite database (default: law_library.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed the job queue with initial discovery jobs')
    seed_parser.add_argument('--all', action='store_true', help='Seed all content types')
    seed_parser.add_argument('--uscode', action='store_true', help='Seed US Code')
    seed_parser.add_argument('--cfr', action='store_true', help='Seed Code of Federal Regulations')
    seed_parser.add_argument('--scotus', action='store_true', help='Seed Supreme Court cases')
    seed_parser.add_argument('--constitution', action='store_true', help='Seed US Constitution')
    seed_parser.add_argument('--federal_rules', action='store_true', help='Seed Federal Rules')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run the worker pool')
    run_parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker threads (default: 1, recommended: 1-2 due to rate limits)'
    )
    run_parser.add_argument(
        '--delay',
        type=float,
        default=10.0,
        help='Delay between requests in seconds (default: 10.0 per robots.txt)'
    )

    # Stats command
    subparsers.add_parser('stats', help='Show statistics')

    # Reset command
    subparsers.add_parser('reset', help='Reset stuck jobs to pending status')

    args = parser.parse_args()

    # Check if database exists
    db_path = Path(args.db)
    db_exists = db_path.exists()

    # Initialize database
    db = Database(args.db)

    if not db_exists:
        logger.info(f"Created new database at {args.db}")

    # Handle commands
    if args.command == 'seed':
        content_types = []
        if args.all:
            content_types.append('all')
        else:
            if args.uscode:
                content_types.append('uscode')
            if args.cfr:
                content_types.append('cfr')
            if args.scotus:
                content_types.append('scotus')
            if args.constitution:
                content_types.append('constitution')
            if args.federal_rules:
                content_types.append('federal_rules')

        if not content_types:
            logger.error("No content types specified. Use --all or specific flags.")
            sys.exit(1)

        seed_jobs(db, content_types)
        show_stats(db)

    elif args.command == 'run':
        if args.workers > 3:
            logger.warning(
                "Using more than 3 workers may violate rate limits. "
                "Consider using 1-2 workers with the 10-second delay."
            )

        logger.info(f"Starting {args.workers} worker(s) with {args.delay}s delay...")
        rate_limiter = RateLimiter(delay_seconds=args.delay)
        worker_pool = WorkerPool(args.workers, db, rate_limiter)

        try:
            worker_pool.start()
            worker_pool.wait_for_completion()
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user")
        finally:
            worker_pool.stop()

        show_stats(db)

    elif args.command == 'stats':
        show_stats(db)

    elif args.command == 'reset':
        count = reset_stuck_jobs(db)
        print(f"Reset {count} stuck jobs to pending status")
        show_stats(db)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
