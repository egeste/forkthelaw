#!/bin/bash
# Test script to simulate the GitHub Actions workflow locally

set -e

echo "======================================"
echo "Testing GitHub Actions Workflow Locally"
echo "======================================"
echo

# Check if database exists
if [ -f law_library.db ]; then
    echo "✓ Found existing database"
    BACKUP_NAME="law_library_backup_$(date +%Y%m%d_%H%M%S).db"
    echo "  Creating backup: $BACKUP_NAME"
    cp law_library.db "$BACKUP_NAME"
else
    echo "✗ No existing database found"
    echo "  Initializing new database..."
    python cli.py seed --all
fi

echo
echo "Resetting stuck jobs..."
python cli.py reset

echo
echo "======================================"
echo "Starting Crawler (3 minute test run)"
echo "======================================"
echo

# Run crawler for 3 minutes (for testing)
# In actual workflow, this would be 180 minutes
timeout 180s python cli.py run --workers 2 --delay 10.0 || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo
        echo "✓ Crawler stopped after 3 minutes (timeout reached)"
    else
        echo
        echo "✗ Crawler failed with exit code $EXIT_CODE"
        exit $EXIT_CODE
    fi
}

echo
echo "======================================"
echo "Final Statistics"
echo "======================================"
echo
python cli.py stats

echo
echo "Database size:"
ls -lh law_library.db

echo
echo "======================================"
echo "Testing compression..."
echo "======================================"
gzip -k law_library.db
echo "Compressed size:"
ls -lh law_library.db.gz

echo
echo "======================================"
echo "Test Complete!"
echo "======================================"
echo
echo "Next steps:"
echo "1. Review the statistics above"
echo "2. If everything looks good, commit and push:"
echo "   git add .github/ GITHUB_ACTIONS.md README.md"
echo "   git commit -m 'Add GitHub Actions automated crawling'"
echo "   git push"
echo "3. Enable GitHub Actions in repository settings"
echo "4. Workflow will run automatically at 2 AM UTC daily"
echo
echo "To trigger manually:"
echo "   gh workflow run crawl.yml"
echo

# Clean up
rm -f law_library.db.gz
