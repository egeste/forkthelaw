"""
Pydantic schema validators for parsed federal records.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class UscSectionRecord(BaseModel):
    """USC Section parsed record."""
    usc_id: str
    title: int
    section: str
    heading: Optional[str] = None
    text: Optional[str] = None
    notes_json: Optional[str] = None
    release_date: Optional[date] = None
    source_path: str
    sha256: str


class PublicLawRecord(BaseModel):
    """Public Law parsed record."""
    pl_id: str
    congress: int
    number: int
    enactment_date: Optional[date] = None
    stat_cites_json: Optional[str] = None
    title: Optional[str] = None
    text: Optional[str] = None
    source_path: str
    sha256: str


class StatPageRecord(BaseModel):
    """Statutes at Large page record."""
    stat_id: str
    volume: int
    page: int
    year: Optional[int] = None
    text: Optional[str] = None
    source_path: str
    sha256: str


class CfrUnitRecord(BaseModel):
    """CFR Unit parsed record."""
    cfr_id: str
    title: int
    part: int
    section: Optional[str] = None
    heading: Optional[str] = None
    text: Optional[str] = None
    effective_date: Optional[date] = None
    source: str = "govinfo"  # or "ecfr"
    source_path: str
    sha256: str


class EcfrVersionRecord(BaseModel):
    """eCFR version record."""
    cfr_id: str
    version_date: date
    text_hash: str
    delta_json: Optional[str] = None
    source_path: Optional[str] = None


class FrDocumentRecord(BaseModel):
    """Federal Register document record."""
    fr_id: str
    publication_date: date
    doc_type: Optional[str] = None
    docket_id: Optional[str] = None
    agency: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    cites_json: Optional[str] = None
    links_json: Optional[str] = None
    source_path: Optional[str] = None
    sha256: str


class BillRecord(BaseModel):
    """Bill parsed record."""
    bill_id: str
    congress: int
    chamber: str  # 'h' or 's'
    number: int
    title: Optional[str] = None
    status: Optional[str] = None
    introduced_date: Optional[date] = None
    latest_action_json: Optional[str] = None
    subjects_json: Optional[str] = None
    source_path: Optional[str] = None
    sha256: str


class BillVersionRecord(BaseModel):
    """Bill version (text snapshot) record."""
    bill_id: str
    version_code: str
    date: Optional[date] = None
    text: Optional[str] = None
    format: Optional[str] = None
    source_path: Optional[str] = None
    sha256: str


class BillEventRecord(BaseModel):
    """Bill event record."""
    bill_id: str
    event_time: datetime
    event_type: str
    body_json: Optional[str] = None


class EdgeRecord(BaseModel):
    """Edge (relationship) record."""
    src_id: str
    src_type: str
    dst_id: str
    dst_type: str
    rel_type: str
    meta_json: Optional[str] = None
