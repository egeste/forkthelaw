# Federal Corpus Seed Data

This directory can contain seed data for testing federal ingestion pipelines without network access.

## Structure

Organize seed files by source:

```
seeds/
  usc/
    title_21_sample.xml
  cfr/
    21_cfr_1308_sample.xml
  fr/
    2023_12345_sample.json
  bills/
    118_hr_1_sample.xml
```

## Usage

Ingestors can check for seed files when in `--limit` mode to enable offline smoke tests.

Example:
```python
seed_path = Path(__file__).parent / "sql" / "seeds" / "usc" / "title_21_sample.xml"
if seed_path.exists():
    # Use seed data
    pass
else:
    # Fetch from network
    pass
```
