"""
Worker pool for processing jobs from the queue.
"""

import threading
import time
import logging
from typing import Optional
import signal
import sys

from database import Database
from scraper import Scraper
from rate_limiter import RateLimiter
from jobs import JOB_REGISTRY


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Worker(threading.Thread):
    """Worker thread that processes jobs from the queue."""

    def __init__(self, worker_id: int, database: Database, scraper: Scraper,
                 stop_event: threading.Event):
        """
        Initialize worker thread.

        Args:
            worker_id: Unique identifier for this worker
            database: Database instance
            scraper: Scraper instance
            stop_event: Event to signal worker to stop
        """
        super().__init__(daemon=True)
        self.worker_id = worker_id
        self.db = database
        self.scraper = scraper
        self.stop_event = stop_event
        self.jobs_processed = 0
        self.name = f"Worker-{worker_id}"

    def run(self):
        """Main worker loop - processes jobs until stop event is set."""
        logger.info(f"{self.name} started")

        while not self.stop_event.is_set():
            try:
                # Get next job from queue
                job = self.db.get_next_job()

                if not job:
                    # No jobs available, wait a bit
                    time.sleep(5)
                    continue

                # Process the job
                self.process_job(job)
                self.jobs_processed += 1

            except Exception as e:
                logger.error(f"{self.name} error: {e}", exc_info=True)
                time.sleep(5)

        logger.info(f"{self.name} stopped. Processed {self.jobs_processed} jobs.")

    def process_job(self, job: dict):
        """
        Process a single job.

        Args:
            job: Job dictionary from queue
        """
        job_id = job['id']
        job_type = job['job_type']
        url = job['url']

        logger.info(f"{self.name} processing job {job_id}: {job_type} - {url}")

        try:
            # Get handler for this job type
            handler_class = JOB_REGISTRY.get(job_type)
            if not handler_class:
                raise ValueError(f"Unknown job type: {job_type}")

            # Create handler and process job
            handler = handler_class(self.scraper, self.db)
            result = handler.handle(job)

            # Mark job as complete
            if result.get('status') == 'success':
                self.db.complete_job(job_id, 'success', result)
                logger.info(f"{self.name} completed job {job_id}")
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"{self.name} job {job_id} failed: {error}")

                # Retry if not too many attempts
                if job.get('attempts', 0) < 3:
                    self.db.retry_job(job_id)
                    logger.info(f"{self.name} will retry job {job_id}")
                else:
                    self.db.complete_job(job_id, 'failed', error=error)
                    logger.error(f"{self.name} gave up on job {job_id} after max retries")

        except Exception as e:
            error_msg = f"Exception processing job: {str(e)}"
            logger.error(f"{self.name} {error_msg}", exc_info=True)

            # Retry if not too many attempts
            if job.get('attempts', 0) < 3:
                self.db.retry_job(job_id)
            else:
                self.db.complete_job(job_id, 'failed', error=error_msg)


class WorkerPool:
    """Manages a pool of worker threads."""

    def __init__(self, num_workers: int, database: Database,
                 rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize worker pool.

        Args:
            num_workers: Number of worker threads to create
            database: Database instance
            rate_limiter: Optional rate limiter (creates default if not provided)
        """
        self.num_workers = num_workers
        self.db = database
        self.rate_limiter = rate_limiter or RateLimiter(delay_seconds=10.0)
        self.scraper = Scraper(self.rate_limiter)
        self.stop_event = threading.Event()
        self.workers = []
        self.stats_thread = None

    def start(self):
        """Start all worker threads."""
        logger.info(f"Starting worker pool with {self.num_workers} workers...")

        # Create and start worker threads
        for i in range(self.num_workers):
            worker = Worker(i + 1, self.db, self.scraper, self.stop_event)
            worker.start()
            self.workers.append(worker)

        # Start stats reporting thread
        self.stats_thread = threading.Thread(target=self._report_stats, daemon=True)
        self.stats_thread.start()

        logger.info("Worker pool started")

    def stop(self):
        """Stop all worker threads gracefully."""
        logger.info("Stopping worker pool...")
        self.stop_event.set()

        # Wait for all workers to finish
        for worker in self.workers:
            worker.join(timeout=30)

        logger.info("Worker pool stopped")

    def _report_stats(self):
        """Periodically report statistics."""
        while not self.stop_event.is_set():
            time.sleep(60)  # Report every minute

            try:
                stats = self.db.get_queue_stats()
                total_processed = sum(w.jobs_processed for w in self.workers)

                logger.info("=" * 60)
                logger.info("QUEUE STATISTICS")
                logger.info(f"  Pending jobs: {stats.get('pending', 0)}")
                logger.info(f"  Processing jobs: {stats.get('processing', 0)}")
                logger.info(f"  Completed jobs: {stats.get('completed', 0)}")
                logger.info(f"  Failed jobs: {stats.get('failed', 0)}")
                logger.info(f"  Total processed this session: {total_processed}")
                logger.info("=" * 60)
            except Exception as e:
                logger.error(f"Error reporting stats: {e}")

    def wait_for_completion(self, check_interval: int = 10):
        """
        Wait until all jobs are completed or failed.

        Args:
            check_interval: Seconds between queue checks
        """
        logger.info("Waiting for all jobs to complete...")

        while not self.stop_event.is_set():
            stats = self.db.get_queue_stats()
            pending = stats.get('pending', 0)
            processing = stats.get('processing', 0)

            if pending == 0 and processing == 0:
                logger.info("All jobs completed!")
                break

            time.sleep(check_interval)


def signal_handler(signum, frame, worker_pool: WorkerPool):
    """Handle interrupt signals gracefully."""
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    worker_pool.stop()
    sys.exit(0)


def run_workers(num_workers: int = 1, database_path: str = "law_library.db"):
    """
    Run the worker pool.

    Args:
        num_workers: Number of worker threads
        database_path: Path to SQLite database
    """
    # Initialize components
    db = Database(database_path)
    rate_limiter = RateLimiter(delay_seconds=10.0)
    worker_pool = WorkerPool(num_workers, db, rate_limiter)

    # Setup signal handlers
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, worker_pool))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, worker_pool))

    # Start workers
    worker_pool.start()

    try:
        # Wait for completion or interrupt
        worker_pool.wait_for_completion()
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    finally:
        worker_pool.stop()


if __name__ == '__main__':
    run_workers(num_workers=1)
