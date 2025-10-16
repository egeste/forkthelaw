"""
USC (United States Code) OLRC USLM XML ingestor.

Source: https://uscode.house.gov/download/download.shtml
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from federal.common import HttpClient, compute_sha256
from federal.identifiers import UscId
from federal.storage import get_storage
from federal.schema_validators import UscSectionRecord


logger = logging.getLogger(__name__)


def discover(state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Discover USC titles available for download.

    Args:
        state: Previous ingestion state

    Returns:
        List of items to fetch (one per title)
    """
    # TODO: Scrape https://uscode.house.gov/download/download.shtml
    # or use direct XML package URLs
    logger.warning("USC discovery not fully implemented - using smoke test data")

    # Return smoke test items for titles 1-5
    items = []
    for title in range(1, 6):
        items.append({
            'title': title,
            'url': f'https://uscode.house.gov/download/releasepoints/us/pl/118/1/xml_usc{title:02d}@118-1.zip',
            'format': 'USLM-XML'
        })

    return items[:5] if state and state.get('limit') else items


def fetch(item: Dict[str, Any], storage) -> Dict[str, Any]:
    """
    Fetch USC XML package.

    Args:
        item: Item from discover()
        storage: Storage backend

    Returns:
        Metadata about fetched content
    """
    title = item['title']
    url = item['url']

    # TODO: Download and extract ZIP to storage
    logger.warning(f"USC fetch not fully implemented for title {title}")

    dest_path = f"usc/title_{title:02d}/raw.zip"
    # client = HttpClient()
    # sha256 = client.download(url, Path(storage.base_path) / dest_path)

    return {
        'title': title,
        'dest_path': dest_path,
        'sha256': 'placeholder',
        'status': 'not_implemented'
    }


def parse(raw: Dict[str, Any]) -> List[UscSectionRecord]:
    """
    Parse USC USLM XML into section records.

    Args:
        raw: Metadata from fetch()

    Returns:
        List of validated USC section records
    """
    # TODO: Parse USLM XML using lxml
    # Extract sections, headings, text
    logger.warning("USC parse not fully implemented")

    title = raw['title']
    # Create a placeholder record
    records = [
        UscSectionRecord(
            usc_id=f"usc:{title}:1",
            title=title,
            section="1",
            heading="Placeholder Section",
            text="Placeholder text for smoke test",
            notes_json=json.dumps({}),
            release_date=None,
            source_path=raw['dest_path'],
            sha256=compute_sha256(b"placeholder")
        )
    ]

    return records


def upsert(records: List[UscSectionRecord], session) -> Dict[str, Any]:
    """
    Upsert USC section records into database.

    Args:
        records: Validated section records
        session: Database connection

    Returns:
        Summary statistics
    """
    inserted = 0
    updated = 0

    with session.get_connection() as conn:
        cursor = conn.cursor()

        for record in records:
            # Check if exists
            cursor.execute("SELECT id FROM usc_section WHERE usc_id = ?", (record.usc_id,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE usc_section
                    SET title = ?, section = ?, heading = ?, text = ?,
                        notes_json = ?, release_date = ?, source_path = ?,
                        sha256 = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE usc_id = ?
                """, (
                    record.title, record.section, record.heading, record.text,
                    record.notes_json, record.release_date, record.source_path,
                    record.sha256, record.usc_id
                ))
                updated += 1
            else:
                cursor.execute("""
                    INSERT INTO usc_section
                    (usc_id, title, section, heading, text, notes_json,
                     release_date, source_path, sha256)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.usc_id, record.title, record.section, record.heading,
                    record.text, record.notes_json, record.release_date,
                    record.source_path, record.sha256
                ))
                inserted += 1

    logger.info(f"USC upsert complete: {inserted} inserted, {updated} updated")
    return {'inserted': inserted, 'updated': updated}


def run_pipeline(db, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Run full USC ingestion pipeline.

    Args:
        db: Database instance
        limit: Optional limit on titles to process

    Returns:
        Summary statistics
    """
    logger.info("Starting USC ingestion pipeline")

    state = db.get_ingestion_state('usc_olrc') or {}
    if limit:
        state['limit'] = limit

    storage = get_storage()

    # Discover
    items = discover(state)
    if limit:
        items = items[:limit]

    logger.info(f"Discovered {len(items)} USC titles")

    # Fetch, parse, upsert
    total_inserted = 0
    total_updated = 0

    for item in items:
        try:
            raw = fetch(item, storage)
            records = parse(raw)
            result = upsert(records, db)

            total_inserted += result['inserted']
            total_updated += result['updated']

        except Exception as e:
            logger.error(f"Failed to process USC title {item['title']}: {e}")

    # Update state
    db.upsert_ingestion_state('usc_olrc', state, success=True)

    summary = {
        'source': 'usc_olrc',
        'items_processed': len(items),
        'records_inserted': total_inserted,
        'records_updated': total_updated
    }

    logger.info(f"USC ingestion complete: {summary}")
    return summary
