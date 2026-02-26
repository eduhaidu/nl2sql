-- NL2SQL PostgreSQL Schema Initialization
-- Run this script to create the required tables for conversation management

-- Conversations table - stores each database import session
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    db_url TEXT NOT NULL,
    database_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Conversation history table - stores all messages (user and assistant)
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    sender VARCHAR(50) NOT NULL CHECK (sender IN ('user', 'assistant')),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Query results table - stores executed SQL queries and their results
CREATE TABLE IF NOT EXISTS query_results (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sql_query TEXT NOT NULL,
    result TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_conversation_history_conversation_id 
    ON conversation_history(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_history_timestamp 
    ON conversation_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_query_results_conversation_id 
    ON query_results(conversation_id);

CREATE INDEX IF NOT EXISTS idx_query_results_created_at 
    ON query_results(created_at);

-- Display confirmation
SELECT 'Schema initialization completed successfully!' as status;
