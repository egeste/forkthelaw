-- Convenience views for federal corpus queries

-- Latest USC sections (most recent version by sha256)
CREATE VIEW IF NOT EXISTS v_usc_latest AS
SELECT u.*
FROM usc_section u
INNER JOIN (
    SELECT usc_id, MAX(updated_at) as max_updated
    FROM usc_section
    GROUP BY usc_id
) latest ON u.usc_id = latest.usc_id AND u.updated_at = latest.max_updated;

-- Latest CFR units (most recent effective date)
CREATE VIEW IF NOT EXISTS v_cfr_latest AS
SELECT c.*
FROM cfr_unit c
INNER JOIN (
    SELECT cfr_id, MAX(effective_date) as max_effective
    FROM cfr_unit
    GROUP BY cfr_id
) latest ON c.cfr_id = latest.cfr_id AND c.effective_date = latest.max_effective;

-- Point-in-time CFR reconstruction helper
-- (Application code should overlay ecfr_version deltas)
CREATE VIEW IF NOT EXISTS v_cfr_baseline AS
SELECT
    cfr_id,
    title,
    part,
    section,
    heading,
    text,
    effective_date,
    source
FROM cfr_unit
WHERE source = 'govinfo';

-- Bill summary with latest version
CREATE VIEW IF NOT EXISTS v_bill_summary AS
SELECT
    b.*,
    bv.version_code as latest_version,
    bv.date as latest_version_date
FROM bill b
LEFT JOIN bill_version bv ON b.bill_id = bv.bill_id
WHERE bv.date = (
    SELECT MAX(date)
    FROM bill_version
    WHERE bill_id = b.bill_id
);

-- Edge statistics
CREATE VIEW IF NOT EXISTS v_edge_stats AS
SELECT
    rel_type,
    src_type,
    dst_type,
    COUNT(*) as edge_count
FROM edge
GROUP BY rel_type, src_type, dst_type;

-- Ingestion health check
CREATE VIEW IF NOT EXISTS v_ingestion_health AS
SELECT
    source,
    last_success,
    CAST((julianday('now') - julianday(last_success)) AS INTEGER) as days_since_success,
    CASE
        WHEN julianday('now') - julianday(last_success) > 7 THEN 'stale'
        WHEN last_success IS NULL THEN 'never_run'
        ELSE 'healthy'
    END as status
FROM ingestion_state;
