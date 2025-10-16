"""
Smoke tests for federal ingestion pipelines.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Import after setting up test environment
def setup_test_db():
    """Create a temporary test database."""
    from database import Database
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    return db, path


def test_usc_pipeline_smoke():
    """Smoke test for USC pipeline."""
    from federal import usc_olrc

    db, db_path = setup_test_db()
    try:
        result = usc_olrc.run_pipeline(db, limit=1)
        assert 'source' in result
        assert result['source'] == 'usc_olrc'
    finally:
        os.unlink(db_path)


def test_cfr_pipeline_smoke():
    """Smoke test for CFR pipeline."""
    from federal import cfr_govinfo

    db, db_path = setup_test_db()
    try:
        result = cfr_govinfo.run_pipeline(db, limit=1)
        assert 'source' in result
        assert result['source'] == 'cfr_govinfo'
    finally:
        os.unlink(db_path)


def test_fr_pipeline_smoke():
    """Smoke test for Federal Register pipeline."""
    from federal import federal_register

    db, db_path = setup_test_db()
    try:
        result = federal_register.run_pipeline(db, limit=1)
        assert 'source' in result
        assert result['source'] == 'federal_register'
    finally:
        os.unlink(db_path)


def test_database_schema():
    """Test that federal tables are created."""
    db, db_path = setup_test_db()
    try:
        stats = db.get_federal_stats()
        assert 'USC Sections' in stats
        assert 'CFR Units' in stats
        assert 'FR Documents' in stats
        assert 'Edges' in stats
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
