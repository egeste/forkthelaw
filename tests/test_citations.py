"""
Tests for citation extraction from legal text.
"""

import pytest
from federal.citations import (
    extract_usc_citations,
    extract_cfr_citations,
    extract_pl_citations,
    extract_all_citations
)


def test_extract_usc_citations():
    """Test extracting USC citations from text."""
    text = """
    This statute is codified at 21 U.S.C. § 841 and also references 18 USC 922.
    """
    citations = extract_usc_citations(text)

    assert len(citations) == 2
    assert citations[0]['usc_id'] == 'usc:21:841'
    assert citations[0]['title'] == 21
    assert citations[0]['section'] == '841'

    assert citations[1]['usc_id'] == 'usc:18:922'
    assert citations[1]['title'] == 18


def test_extract_cfr_citations():
    """Test extracting CFR citations."""
    text = "See 21 CFR § 1308.12 and also 21 C.F.R. 1308.11 for more details."
    citations = extract_cfr_citations(text)

    assert len(citations) == 2
    assert 'cfr:21:1308' in citations[0]['cfr_id']


def test_extract_pl_citations():
    """Test extracting Public Law citations."""
    text = "Enacted as Pub. L. No. 117-328 and amended by Public Law 118-5."
    citations = extract_pl_citations(text)

    assert len(citations) == 2
    assert citations[0]['pl_id'] == 'pl:117-328'
    assert citations[1]['pl_id'] == 'pl:118-5'


def test_extract_all_citations():
    """Test extracting all citation types at once."""
    text = """
    This regulation at 21 CFR § 1308.12 implements 21 U.S.C. § 841,
    as enacted by Pub. L. No. 91-513, 84 Stat. 1242.
    See also 87 Fed. Reg. 12345.
    """
    all_cites = extract_all_citations(text)

    assert len(all_cites['usc']) >= 1
    assert len(all_cites['cfr']) >= 1
    assert len(all_cites['public_laws']) >= 1
    assert len(all_cites['statutes']) >= 1
    assert len(all_cites['federal_register']) >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
