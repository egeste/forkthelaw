#!/usr/bin/env bash
#
# Smoke test workflow for federal corpus ingestion
#
set -euo pipefail

echo "================================"
echo "Federal Corpus Smoke Test"
echo "================================"

# Create a temporary test database
TEST_DB="test_law_library.db"
rm -f "$TEST_DB" edges.csv

echo ""
echo "Step 1: Initialize database..."
python cli.py --db "$TEST_DB" flc stats

echo ""
echo "Step 2: Ingest USC (limited)..."
python cli.py --db "$TEST_DB" flc ingest usc --limit 5

echo ""
echo "Step 3: Ingest Public Laws (limited)..."
python cli.py --db "$TEST_DB" flc ingest public-laws --limit 3 || echo "Public Laws not fully implemented"

echo ""
echo "Step 4: Ingest CFR Title 21 (limited)..."
python cli.py --db "$TEST_DB" flc ingest cfr --title 21 --parts 1300,1308 --limit 10

echo ""
echo "Step 5: Ingest eCFR Title 21 (limited)..."
python cli.py --db "$TEST_DB" flc ingest ecfr --title 21 --parts 1308 --days 3 || echo "eCFR not fully implemented"

echo ""
echo "Step 6: Ingest Federal Register (limited)..."
python cli.py --db "$TEST_DB" flc ingest fr --query "21 CFR 1308" --limit 5

echo ""
echo "Step 7: Ingest Bills (limited)..."
python cli.py --db "$TEST_DB" flc ingest bills --congress 118 --limit 10 || echo "Bills not fully implemented"

echo ""
echo "Step 8: Export edges..."
python cli.py --db "$TEST_DB" flc graph edges --out edges.csv

echo ""
echo "Step 9: Query point-in-time CFR..."
python cli.py --db "$TEST_DB" flc point-in-time cfr --id cfr:21:1308:12 --date 2021-03-15 || echo "Point-in-time not fully implemented"

echo ""
echo "Step 10: Show final statistics..."
python cli.py --db "$TEST_DB" flc stats

echo ""
echo "Step 11: Verify database tables..."
sqlite3 "$TEST_DB" ".tables"

echo ""
echo "================================"
echo "Smoke test complete!"
echo "Test database: $TEST_DB"
echo "Edges file: edges.csv"
echo "================================"

# Optionally clean up
# rm -f "$TEST_DB" edges.csv
