-- Initialize database schema and create default data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_transcripts_created_at ON transcripts(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_transcript_id ON tasks(transcript_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_usage_logs_api_key_id ON usage_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);

-- Create a default API key for initial testing (hashed version of 'sk-default-test-key')
INSERT INTO api_keys (key_hash, name, active, created_by) 
VALUES (
    'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
    'Default Test Key',
    true,
    'system'
) ON CONFLICT (key_hash) DO NOTHING;
