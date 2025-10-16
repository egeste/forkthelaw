-- Federal corpus database schema
-- SQLite-first design with Postgres compatibility

-- USC (United States Code) sections
CREATE TABLE IF NOT EXISTS usc_section (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usc_id TEXT NOT NULL UNIQUE,
    title INTEGER NOT NULL,
    section TEXT NOT NULL,
    heading TEXT,
    text TEXT,
    notes_json TEXT,
    release_date DATE,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usc_title ON usc_section(title);
CREATE INDEX IF NOT EXISTS idx_usc_section ON usc_section(title, section);
CREATE INDEX IF NOT EXISTS idx_usc_sha256 ON usc_section(sha256);

-- Public Laws
CREATE TABLE IF NOT EXISTS public_law (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pl_id TEXT NOT NULL UNIQUE,
    congress INTEGER NOT NULL,
    number INTEGER NOT NULL,
    enactment_date DATE,
    stat_cites_json TEXT,
    title TEXT,
    text TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pl_congress ON public_law(congress);
CREATE INDEX IF NOT EXISTS idx_pl_enactment ON public_law(enactment_date);

-- Statutes at Large pages
CREATE TABLE IF NOT EXISTS stat_page (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_id TEXT NOT NULL UNIQUE,
    volume INTEGER NOT NULL,
    page INTEGER NOT NULL,
    year INTEGER,
    text TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stat_volume ON stat_page(volume, page);

-- CFR (Code of Federal Regulations) units
CREATE TABLE IF NOT EXISTS cfr_unit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cfr_id TEXT NOT NULL,
    title INTEGER NOT NULL,
    part INTEGER NOT NULL,
    section TEXT,
    heading TEXT,
    text TEXT,
    effective_date DATE,
    source TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cfr_id, effective_date)
);

CREATE INDEX IF NOT EXISTS idx_cfr_title_part ON cfr_unit(title, part);
CREATE INDEX IF NOT EXISTS idx_cfr_effective ON cfr_unit(effective_date);
CREATE INDEX IF NOT EXISTS idx_cfr_id ON cfr_unit(cfr_id);

-- eCFR versions (daily point-in-time)
CREATE TABLE IF NOT EXISTS ecfr_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cfr_id TEXT NOT NULL,
    version_date DATE NOT NULL,
    text_hash TEXT NOT NULL,
    delta_json TEXT,
    source_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cfr_id, version_date)
);

CREATE INDEX IF NOT EXISTS idx_ecfr_cfr_id ON ecfr_version(cfr_id, version_date);

-- Federal Register documents
CREATE TABLE IF NOT EXISTS fr_document (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fr_id TEXT NOT NULL UNIQUE,
    publication_date DATE NOT NULL,
    doc_type TEXT,
    docket_id TEXT,
    agency TEXT,
    title TEXT,
    summary TEXT,
    cites_json TEXT,
    links_json TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fr_date ON fr_document(publication_date);
CREATE INDEX IF NOT EXISTS idx_fr_agency ON fr_document(agency);
CREATE INDEX IF NOT EXISTS idx_fr_type ON fr_document(doc_type);

-- Bills
CREATE TABLE IF NOT EXISTS bill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id TEXT NOT NULL UNIQUE,
    congress INTEGER NOT NULL,
    chamber TEXT NOT NULL,
    number INTEGER NOT NULL,
    title TEXT,
    status TEXT,
    introduced_date DATE,
    latest_action_json TEXT,
    subjects_json TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bill_congress ON bill(congress);
CREATE INDEX IF NOT EXISTS idx_bill_chamber ON bill(congress, chamber);

-- Bill versions (text snapshots)
CREATE TABLE IF NOT EXISTS bill_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id TEXT NOT NULL,
    version_code TEXT NOT NULL,
    date DATE,
    text TEXT,
    format TEXT,
    source_path TEXT,
    sha256 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bill_id, version_code),
    FOREIGN KEY (bill_id) REFERENCES bill(bill_id)
);

CREATE INDEX IF NOT EXISTS idx_bill_version_bill ON bill_version(bill_id);

-- Bill events (actions, votes, etc.)
CREATE TABLE IF NOT EXISTS bill_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id TEXT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    body_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bill(bill_id)
);

CREATE INDEX IF NOT EXISTS idx_bill_event_bill ON bill_event(bill_id, event_time);

-- Edge table for relationships
CREATE TABLE IF NOT EXISTS edge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id TEXT NOT NULL,
    src_type TEXT NOT NULL,
    dst_id TEXT NOT NULL,
    dst_type TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    meta_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(src_id, dst_id, rel_type)
);

CREATE INDEX IF NOT EXISTS idx_edge_src ON edge(src_id, src_type);
CREATE INDEX IF NOT EXISTS idx_edge_dst ON edge(dst_id, dst_type);
CREATE INDEX IF NOT EXISTS idx_edge_rel ON edge(rel_type);

-- Ingestion state tracking
CREATE TABLE IF NOT EXISTS ingestion_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL UNIQUE,
    last_run TIMESTAMP,
    last_success TIMESTAMP,
    state_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_source ON ingestion_state(source);
