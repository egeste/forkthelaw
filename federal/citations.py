"""
Citation extraction from legal text.

Extracts structured citations from free-form text and normalizes them
using the identifiers module.
"""

import re
from typing import List, Dict, Any
from federal.identifiers import (
    parse_usc_cite,
    parse_cfr_cite,
    parse_pl_cite,
    parse_stat_cite,
    parse_fr_cite
)


# Compiled regex patterns for efficiency
USC_PATTERN = re.compile(r'(\d+)\s*U\.?S\.?C\.?\s*§?\s*([\d\w\.\-]+)', re.IGNORECASE)
CFR_PATTERN = re.compile(r'(\d+)\s*C\.?F\.?R\.?\s*§?\s*([\d\w\.\-]+)', re.IGNORECASE)
PL_PATTERN = re.compile(r'Pub\.?\s*L\.?\s*(?:No\.?)?\s*(\d+)-(\d+)', re.IGNORECASE)
STAT_PATTERN = re.compile(r'(\d+)\s*Stat\.?\s*(\d+)', re.IGNORECASE)
FR_PATTERN = re.compile(r'(\d+)\s*Fed\.?\s*Reg\.?\s*(\d+)', re.IGNORECASE)


def extract_usc_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract all USC citations from text.

    Returns:
        List of dicts with keys: usc_id, title, section, match
    """
    citations = []
    for match in USC_PATTERN.finditer(text):
        result = parse_usc_cite(match.group(0))
        if result:
            usc_id, title, section = result
            citations.append({
                'usc_id': usc_id,
                'title': title,
                'section': section,
                'match': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    return citations


def extract_cfr_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract all CFR citations from text.

    Returns:
        List of dicts with keys: cfr_id, title, part_section, match
    """
    citations = []
    for match in CFR_PATTERN.finditer(text):
        result = parse_cfr_cite(match.group(0))
        if result:
            cfr_id, title, part_section = result
            citations.append({
                'cfr_id': cfr_id,
                'title': title,
                'part_section': part_section,
                'match': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    return citations


def extract_pl_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract all Public Law citations from text.

    Returns:
        List of dicts with keys: pl_id, congress, number, match
    """
    citations = []
    for match in PL_PATTERN.finditer(text):
        result = parse_pl_cite(match.group(0))
        if result:
            pl_id, congress, number = result
            citations.append({
                'pl_id': pl_id,
                'congress': congress,
                'number': number,
                'match': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    return citations


def extract_stat_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract all Statutes at Large citations from text.

    Returns:
        List of dicts with keys: stat_id, volume, page, match
    """
    citations = []
    for match in STAT_PATTERN.finditer(text):
        result = parse_stat_cite(match.group(0))
        if result:
            stat_id, volume, page = result
            citations.append({
                'stat_id': stat_id,
                'volume': volume,
                'page': page,
                'match': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    return citations


def extract_fr_citations(text: str) -> List[Dict[str, Any]]:
    """
    Extract all Federal Register citations from text.

    Returns:
        List of dicts with keys: fr_id, year, page, match
    """
    citations = []
    for match in FR_PATTERN.finditer(text):
        result = parse_fr_cite(match.group(0))
        if result:
            fr_id, year, page = result
            citations.append({
                'fr_id': fr_id,
                'year': year,
                'page': page,
                'match': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    return citations


def extract_all_citations(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract all types of citations from text.

    Returns:
        Dict with keys: usc, cfr, public_laws, statutes, federal_register
    """
    return {
        'usc': extract_usc_citations(text),
        'cfr': extract_cfr_citations(text),
        'public_laws': extract_pl_citations(text),
        'statutes': extract_stat_citations(text),
        'federal_register': extract_fr_citations(text)
    }
