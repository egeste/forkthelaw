"""
Canonical identifier parsing and formatting for federal legal resources.

Supports:
- USC: usc:<title>:<section>
- Public Law: pl:<congress>-<number>
- Statutes at Large: stat:<volume>:<page>
- CFR: cfr:<title>:<part>[:<section>]
- Federal Register: fr:<year>-<document_number>
- Bill: bill:<congress>:<chamber>:<number>
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class UscId:
    """USC identifier."""
    title: int
    section: str

    def __str__(self) -> str:
        return f"usc:{self.title}:{self.section}"

    @classmethod
    def parse(cls, usc_id: str) -> Optional["UscId"]:
        """Parse usc:<title>:<section>"""
        match = re.match(r"^usc:(\d+):([a-zA-Z0-9\.\-]+)$", usc_id)
        if match:
            return cls(title=int(match.group(1)), section=match.group(2))
        return None


@dataclass
class PublicLawId:
    """Public Law identifier."""
    congress: int
    number: int

    def __str__(self) -> str:
        return f"pl:{self.congress}-{self.number}"

    @classmethod
    def parse(cls, pl_id: str) -> Optional["PublicLawId"]:
        """Parse pl:<congress>-<number>"""
        match = re.match(r"^pl:(\d+)-(\d+)$", pl_id)
        if match:
            return cls(congress=int(match.group(1)), number=int(match.group(2)))
        return None


@dataclass
class StatId:
    """Statutes at Large identifier."""
    volume: int
    page: int

    def __str__(self) -> str:
        return f"stat:{self.volume}:{self.page}"

    @classmethod
    def parse(cls, stat_id: str) -> Optional["StatId"]:
        """Parse stat:<volume>:<page>"""
        match = re.match(r"^stat:(\d+):(\d+)$", stat_id)
        if match:
            return cls(volume=int(match.group(1)), page=int(match.group(2)))
        return None


@dataclass
class CfrId:
    """CFR identifier."""
    title: int
    part: int
    section: Optional[str] = None

    def __str__(self) -> str:
        if self.section:
            return f"cfr:{self.title}:{self.part}:{self.section}"
        return f"cfr:{self.title}:{self.part}"

    @classmethod
    def parse(cls, cfr_id: str) -> Optional["CfrId"]:
        """Parse cfr:<title>:<part>[:<section>]"""
        match = re.match(r"^cfr:(\d+):(\d+)(?::([a-zA-Z0-9\.\-]+))?$", cfr_id)
        if match:
            return cls(
                title=int(match.group(1)),
                part=int(match.group(2)),
                section=match.group(3)
            )
        return None


@dataclass
class FrId:
    """Federal Register identifier."""
    year: int
    document_number: int

    def __str__(self) -> str:
        return f"fr:{self.year}-{self.document_number}"

    @classmethod
    def parse(cls, fr_id: str) -> Optional["FrId"]:
        """Parse fr:<year>-<document_number>"""
        match = re.match(r"^fr:(\d{4})-(\d+)$", fr_id)
        if match:
            return cls(year=int(match.group(1)), document_number=int(match.group(2)))
        return None


@dataclass
class BillId:
    """Bill identifier."""
    congress: int
    chamber: str  # 'h' or 's'
    number: int

    def __str__(self) -> str:
        return f"bill:{self.congress}:{self.chamber}:{self.number}"

    @classmethod
    def parse(cls, bill_id: str) -> Optional["BillId"]:
        """Parse bill:<congress>:<chamber>:<number>"""
        match = re.match(r"^bill:(\d+):([hs]):(\d+)$", bill_id)
        if match:
            return cls(
                congress=int(match.group(1)),
                chamber=match.group(2),
                number=int(match.group(3))
            )
        return None


def parse_usc_cite(cite: str) -> Optional[Tuple[str, int, str]]:
    """
    Parse a USC citation like '21 U.S.C. § 841'.

    Returns:
        (usc_id, title, section) or None
    """
    match = re.search(r'(\d+)\s*U\.?S\.?C\.?\s*§?\s*([\d\w\.\-]+)', cite, re.IGNORECASE)
    if match:
        title = int(match.group(1))
        section = match.group(2)
        return (f"usc:{title}:{section}", title, section)
    return None


def parse_cfr_cite(cite: str) -> Optional[Tuple[str, int, str]]:
    """
    Parse a CFR citation like '21 CFR § 1308.12'.

    Returns:
        (cfr_id, title, part_section) or None
    """
    match = re.search(r'(\d+)\s*C\.?F\.?R\.?\s*§?\s*([\d\w\.\-]+)', cite, re.IGNORECASE)
    if match:
        title = int(match.group(1))
        part_section = match.group(2)
        # Split part and section if possible
        parts = part_section.split('.')
        if len(parts) >= 2:
            return (f"cfr:{title}:{parts[0]}:{'.'.join(parts[1:])}", title, part_section)
        return (f"cfr:{title}:{parts[0]}", title, part_section)
    return None


def parse_pl_cite(cite: str) -> Optional[Tuple[str, int, int]]:
    """
    Parse a Public Law citation like 'Pub. L. No. 117-328'.

    Returns:
        (pl_id, congress, number) or None
    """
    match = re.search(r'Pub\.?\s*L\.?\s*(?:No\.?)?\s*(\d+)-(\d+)', cite, re.IGNORECASE)
    if match:
        congress = int(match.group(1))
        number = int(match.group(2))
        return (f"pl:{congress}-{number}", congress, number)
    return None


def parse_stat_cite(cite: str) -> Optional[Tuple[str, int, int]]:
    """
    Parse a Statutes at Large citation like '136 Stat. 4459'.

    Returns:
        (stat_id, volume, page) or None
    """
    match = re.search(r'(\d+)\s*Stat\.?\s*(\d+)', cite, re.IGNORECASE)
    if match:
        volume = int(match.group(1))
        page = int(match.group(2))
        return (f"stat:{volume}:{page}", volume, page)
    return None


def parse_fr_cite(cite: str) -> Optional[Tuple[str, int, int]]:
    """
    Parse a Federal Register citation like '87 Fed. Reg. 12345'.

    Returns:
        (fr_id, year, page) or None
    Note: Year must be inferred from context; page is used as doc number
    """
    match = re.search(r'(\d+)\s*Fed\.?\s*Reg\.?\s*(\d+)', cite, re.IGNORECASE)
    if match:
        volume = int(match.group(1))
        page = int(match.group(2))
        # FR volumes correlate to years (Vol 1 = 1936, Vol 87 = 2022)
        year = 1935 + volume
        return (f"fr:{year}-{page}", year, page)
    return None


def parse_bill_cite(cite: str) -> Optional[Tuple[str, int, str, int]]:
    """
    Parse a bill citation like 'H.R. 1234' or 'S. 567' with congress context.

    Returns:
        (bill_id, congress, chamber, number) or None
    Note: Congress must be provided separately
    """
    match = re.search(r'(H\.?R\.?|S\.?)\s*(\d+)', cite, re.IGNORECASE)
    if match:
        chamber_raw = match.group(1).upper().replace('.', '')
        chamber = 'h' if 'H' in chamber_raw else 's'
        number = int(match.group(2))
        # Cannot determine congress from citation alone
        return (None, 0, chamber, number)  # Caller must fill in congress
    return None
