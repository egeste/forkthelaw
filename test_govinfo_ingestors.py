#!/usr/bin/env python3
"""
Unit tests for GovInfo ingestors (public laws and CFR).
Tests the parsing and data structure logic without requiring live API access.
"""

from lxml import etree

from federal.public_laws import _parse_plaw_id
from federal.cfr_govinfo import _parse_cfr_package_id
from federal.schema_validators import PublicLawRecord, CfrUnitRecord


def test_plaw_id_parsing_house():
    """Test parsing house bill package ID."""
    congress, number = _parse_plaw_id("PLAW-118hr1234")
    assert congress == 118 and number == 1234, f"Expected (118, 1234), got ({congress}, {number})"
    print("✓ PLAW house bill parsing")


def test_plaw_id_parsing_senate():
    """Test parsing senate bill package ID."""
    congress, number = _parse_plaw_id("PLAW-118s567")
    assert congress == 118 and number == 567, f"Expected (118, 567), got ({congress}, {number})"
    print("✓ PLAW senate bill parsing")


def test_plaw_id_parsing_invalid():
    """Test parsing invalid package ID."""
    congress, number = _parse_plaw_id("INVALID-118hr1234")
    assert congress is None and number is None, f"Expected (None, None), got ({congress}, {number})"
    print("✓ PLAW invalid ID handling")


def test_plaw_record_creation():
    """Test creating a PublicLawRecord."""
    record = PublicLawRecord(
        pl_id="pl:118:1234",
        congress=118,
        number=1234,
        enactment_date="2024-01-15",
        stat_cites_json='["138 Stat. 123"]',
        title="An Act to do something",
        text="Full text of the law...",
        source_path="/path/to/file.xml",
        sha256="abc123def456"
    )
    assert record.pl_id == "pl:118:1234"
    assert record.congress == 118
    assert record.number == 1234
    assert record.title == "An Act to do something"
    print("✓ PublicLawRecord creation")


def test_cfr_package_id_parsing():
    """Test parsing CFR package ID."""
    title, part = _parse_cfr_package_id("CFR-2023-title21-part1308")
    assert title == 21 and part == 1308, f"Expected (21, 1308), got ({title}, {part})"
    print("✓ CFR package ID parsing")


def test_cfr_package_id_parsing_title26():
    """Test parsing CFR package ID for Title 26."""
    title, part = _parse_cfr_package_id("CFR-2023-title26-part1")
    assert title == 26 and part == 1, f"Expected (26, 1), got ({title}, {part})"
    print("✓ CFR Title 26 parsing")


def test_cfr_package_id_parsing_invalid():
    """Test parsing invalid CFR package ID."""
    title, part = _parse_cfr_package_id("INVALID-2023-title21-part1308")
    assert title is None and part is None, f"Expected (None, None), got ({title}, {part})"
    print("✓ CFR invalid ID handling")


def test_cfr_record_creation():
    """Test creating a CfrUnitRecord."""
    record = CfrUnitRecord(
        cfr_id="cfr:21:1308:1",
        title=21,
        part=1308,
        section="1",
        heading="Controlled Substances",
        text="The following are scheduled...",
        effective_date="2023-01-01",
        source="govinfo",
        source_path="/path/to/file.xml",
        sha256="abc123def456"
    )
    assert record.cfr_id == "cfr:21:1308:1"
    assert record.title == 21
    assert record.part == 1308
    assert record.section == "1"
    assert record.source == "govinfo"
    print("✓ CfrUnitRecord creation")


def test_simple_plaw_xml_parsing():
    """Test parsing a simple public law XML structure."""
    xml_str = """<?xml version="1.0"?>
<bill>
    <metadata>
        <official-title>An Act to do something</official-title>
        <enactment-date>2024-01-15</enactment-date>
    </metadata>
    <section>
        <section-num>1</section-num>
        <text>This is section text</text>
    </section>
</bill>"""
    root = etree.fromstring(xml_str.encode())

    title_elem = root.find('.//official-title')
    assert title_elem is not None and title_elem.text == "An Act to do something"
    print("✓ Public Law XML parsing")


def test_simple_cfr_xml_parsing():
    """Test parsing a simple CFR XML structure."""
    xml_str = """<?xml version="1.0"?>
<cfr>
    <SECTION>
        <SECTION-NUM>1</SECTION-NUM>
        <SUBJECT>Definitions</SUBJECT>
        <P>These terms shall have the following meanings:</P>
    </SECTION>
    <SECTION>
        <SECTION-NUM>2</SECTION-NUM>
        <SUBJECT>Applicability</SUBJECT>
        <P>This part applies to all persons.</P>
    </SECTION>
</cfr>"""
    root = etree.fromstring(xml_str.encode())

    sections = root.findall('.//SECTION')
    assert len(sections) == 2, f"Expected 2 sections, got {len(sections)}"

    first_section_num = sections[0].find('.//SECTION-NUM')
    assert first_section_num.text == "1"
    print("✓ CFR XML parsing")


if __name__ == '__main__':
    print("\nRunning GovInfo ingestor tests...\n")

    tests = [
        test_plaw_id_parsing_house,
        test_plaw_id_parsing_senate,
        test_plaw_id_parsing_invalid,
        test_plaw_record_creation,
        test_cfr_package_id_parsing,
        test_cfr_package_id_parsing_title26,
        test_cfr_package_id_parsing_invalid,
        test_cfr_record_creation,
        test_simple_plaw_xml_parsing,
        test_simple_cfr_xml_parsing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed\n")
    exit(0 if failed == 0 else 1)
