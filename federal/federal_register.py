"""
Federal Register API ingestor.
"""

import logging
from typing import List, Dict, Any, Optional
import json

from federal.common import compute_sha256
from federal.schema_validators import FrDocumentRecord

logger = logging.getLogger(__name__)


def discover(state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    logger.warning("Federal Register discovery not implemented")
    return [{'fr_id': 'fr:2023-12345', 'query': '21 CFR 1308'}]


def fetch(item: Dict[str, Any], storage) -> Dict[str, Any]:
    logger.warning("Federal Register fetch not implemented")
    return {'status': 'not_implemented', **item}


def parse(raw: Dict[str, Any]) -> List[FrDocumentRecord]:
    from datetime import date
    rec = FrDocumentRecord(
        fr_id=raw.get('fr_id', 'fr:2023-1'),
        publication_date=date(2023, 1, 1),
        doc_type="RULE",
        agency="DEA",
        title="Placeholder FR Document",
        summary="Placeholder",
        source_path="placeholder",
        sha256=compute_sha256(b"placeholder")
    )
    return [rec]


def upsert(records: List[FrDocumentRecord], session) -> Dict[str, Any]:
    inserted = 0
    with session.get_connection() as conn:
        cursor = conn.cursor()
        for rec in records:
            cursor.execute("""
                INSERT OR REPLACE INTO fr_document
                (fr_id, publication_date, doc_type, docket_id, agency, title, summary, cites_json, links_json, source_path, sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rec.fr_id, rec.publication_date, rec.doc_type, rec.docket_id, rec.agency, rec.title,
                  rec.summary, rec.cites_json, rec.links_json, rec.source_path, rec.sha256))
            inserted += 1
    return {'inserted': inserted}


def run_pipeline(db, limit: Optional[int] = None, query: Optional[str] = None) -> Dict[str, Any]:
    logger.info("Federal Register pipeline")
    from federal.storage import get_storage
    state = db.get_ingestion_state('federal_register') or {}
    if query:
        state['query'] = query

    storage = get_storage()
    items = discover(state)
    if limit:
        items = items[:limit]

    total_inserted = 0
    for item in items:
        try:
            raw = fetch(item, storage)
            records = parse(raw)
            result = upsert(records, db)
            total_inserted += result['inserted']
        except Exception as e:
            logger.error(f"FR error: {e}")

    db.upsert_ingestion_state('federal_register', state, success=True)
    return {'source': 'federal_register', 'items_processed': len(items), 'records_inserted': total_inserted}
