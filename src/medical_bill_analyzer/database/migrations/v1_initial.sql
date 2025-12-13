-- Medical Bill Analyzer - Initial Schema (v1)
-- Phase 1: Core functionality with basic bill information

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Insert initial version
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'Initial schema: bills table with basic information');

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    pdf_path TEXT NOT NULL,

    -- Practitioner information
    practitioner_name TEXT,
    practitioner_type TEXT,

    -- Bill details
    bill_date DATE,
    bill_number TEXT,
    total_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'EUR',

    -- Processing metadata
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_status TEXT DEFAULT 'success',
    raw_extraction_json TEXT,
    notes TEXT
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_bill_date ON bills(bill_date);
CREATE INDEX IF NOT EXISTS idx_practitioner_name ON bills(practitioner_name);
CREATE INDEX IF NOT EXISTS idx_practitioner_type ON bills(practitioner_type);
CREATE INDEX IF NOT EXISTS idx_file_hash ON bills(file_hash);
CREATE INDEX IF NOT EXISTS idx_extraction_status ON bills(extraction_status);
