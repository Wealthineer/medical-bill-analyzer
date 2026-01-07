-- Migration v3: Add settings table to store all app configuration
-- Replaces config.yaml with database storage

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Single row table

    -- LLM Configuration
    llm_provider TEXT NOT NULL DEFAULT 'anthropic',

    -- Anthropic settings
    anthropic_model TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
    anthropic_max_tokens INTEGER NOT NULL DEFAULT 1000,
    anthropic_temperature REAL NOT NULL DEFAULT 0.0,

    -- OpenAI settings (also used for LM Studio)
    openai_model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
    openai_max_tokens INTEGER NOT NULL DEFAULT 1000,
    openai_temperature REAL NOT NULL DEFAULT 0.0,
    openai_base_url TEXT,  -- NULL for OpenAI, set for LM Studio

    -- Ollama settings
    ollama_model TEXT NOT NULL DEFAULT 'llama3.1:8b',
    ollama_base_url TEXT NOT NULL DEFAULT 'http://localhost:11434',
    ollama_timeout INTEGER NOT NULL DEFAULT 60,

    -- App settings
    bonus_threshold REAL NOT NULL DEFAULT 1000.0,
    extract_line_items INTEGER NOT NULL DEFAULT 0,  -- 0 = false, 1 = true
    retry_attempts INTEGER NOT NULL DEFAULT 1,

    -- Storage paths
    database_path TEXT NOT NULL,
    pdf_storage_path TEXT NOT NULL,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Create trigger to auto-update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS settings_updated_at
AFTER UPDATE ON settings
FOR EACH ROW
BEGIN
    UPDATE settings SET updated_at = datetime('now') WHERE id = 1;
END;

-- Insert default settings (will only insert if table is empty)
INSERT OR IGNORE INTO settings (
    id,
    llm_provider,
    database_path,
    pdf_storage_path
) VALUES (
    1,
    'anthropic',
    '~/.medical-bill-analyzer/data/medical_bills.db',
    '~/.medical-bill-analyzer/data/pdfs'
);

-- Update schema version
INSERT OR REPLACE INTO schema_version (version, description, applied_at)
VALUES (3, 'Add settings table', datetime('now'));
