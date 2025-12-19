-- Migration v2: Add credentials table for API key storage
-- This allows storing LLM provider credentials in the database instead of environment variables
-- Supports bundled executable deployments where .env files are not appropriate

CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL UNIQUE,  -- 'anthropic', 'openai', or 'ollama'
    api_key TEXT,                    -- API key (NULL for ollama which runs locally)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on provider for fast lookups
CREATE INDEX IF NOT EXISTS idx_credentials_provider ON credentials(provider);

-- Update schema version
UPDATE schema_version SET version = 2 WHERE id = 1;
