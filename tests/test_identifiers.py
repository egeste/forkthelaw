"""
Tests for federal identifier parsing and formatting.
"""

import pytest
from federal.identifiers import (
    UscId, PublicLawId, StatId, CfrId, FrId, BillId,
    parse_usc_cite, parse_cfr_cite, parse_pl_cite,
    parse_stat_cite, parse_fr_cite
)


def test_usc_id():
    """Test USC identifier parsing and formatting."""
    usc_id = UscId(title=21, section="841")
    assert str(usc_id) == "usc:21:841"

    parsed = UscId.parse("usc:21:841")
    assert parsed.title == 21
    assert parsed.section == "841"


def test_public_law_id():
    """Test Public Law identifier."""
    pl_id = PublicLawId(congress=117, number=328)
    assert str(pl_id) == "pl:117-328"

    parsed = PublicLawId.parse("pl:117-328")
    assert parsed.congress == 117
    assert parsed.number == 328


def test_cfr_id():
    """Test CFR identifier."""
    cfr_id = CfrId(title=21, part=1308, section="12")
    assert str(cfr_id) == "cfr:21:1308:12"

    parsed = CfrId.parse("cfr:21:1308:12")
    assert parsed.title == 21
    assert parsed.part == 1308
    assert parsed.section == "12"

    # Test without section
    cfr_id2 = CfrId(title=21, part=1308)
    assert str(cfr_id2) == "cfr:21:1308"


def test_parse_usc_cite():
    """Test parsing USC citations from text."""
    result = parse_usc_cite("21 U.S.C. § 841")
    assert result is not None
    usc_id, title, section = result
    assert usc_id == "usc:21:841"
    assert title == 21
    assert section == "841"

    # Test various formats
    assert parse_usc_cite("21 USC 841") is not None
    assert parse_usc_cite("21 U.S.C. 841") is not None


def test_parse_cfr_cite():
    """Test parsing CFR citations."""
    result = parse_cfr_cite("21 CFR § 1308.12")
    assert result is not None
    cfr_id, title, part_section = result
    assert cfr_id == "cfr:21:1308:12"
    assert title == 21
    assert part_section == "1308.12"


def test_parse_pl_cite():
    """Test parsing Public Law citations."""
    result = parse_pl_cite("Pub. L. No. 117-328")
    assert result is not None
    pl_id, congress, number = result
    assert pl_id == "pl:117-328"
    assert congress == 117
    assert number == 328

    # Test variations
    assert parse_pl_cite("Pub. L. 117-328") is not None
    assert parse_pl_cite("Public Law 117-328") is not None


def test_parse_stat_cite():
    """Test parsing Statutes at Large citations."""
    result = parse_stat_cite("136 Stat. 4459")
    assert result is not None
    stat_id, volume, page = result
    assert stat_id == "stat:136:4459"
    assert volume == 136
    assert page == 4459


def test_parse_fr_cite():
    """Test parsing Federal Register citations."""
    result = parse_fr_cite("87 Fed. Reg. 12345")
    assert result is not None
    fr_id, year, page = result
    # Volume 87 = year 2022 (1935 + 87)
    assert year == 2022
    assert page == 12345


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
