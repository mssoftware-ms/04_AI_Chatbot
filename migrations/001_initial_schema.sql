-- Initial database schema for WhatsApp AI Chatbot
-- SQLite schema with all tables, indexes, triggers, and optimizations
-- Version: 1.0.0

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Configure SQLite for optimal performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;  -- 256MB mmap

-- Projects table: Isolates different chatbot instances
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    name TEXT NOT NULL,
    description TEXT,
    vector_collection_name TEXT NOT NULL UNIQUE,
    settings TEXT DEFAULT '{}',  -- JSON
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table: Groups messages by conversation context
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    contact_name TEXT,
    session_id TEXT,
    context_summary TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',  -- JSON
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

-- Messages table: Stores all chat messages with rich metadata
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    conversation_id TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT NOT NULL CHECK (message_type IN ('user', 'assistant', 'system')),
    whatsapp_message_id TEXT UNIQUE,
    phone_number TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'error')),
    error_message TEXT,
    context_used TEXT,
    tokens_used INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    metadata TEXT DEFAULT '{}',  -- JSON
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);

-- Documents table: RAG system document storage
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'error')),
    chunks_count INTEGER NOT NULL DEFAULT 0,
    vectors_generated BOOLEAN NOT NULL DEFAULT 0,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    last_accessed DATETIME,
    metadata TEXT DEFAULT '{}',  -- JSON
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

-- Document chunks table: Processed text chunks for vector search
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    vector_id TEXT UNIQUE,  -- ChromaDB document ID
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',  -- JSON
    FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
);

-- Memory entries table: Long-term conversation memory
CREATE TABLE IF NOT EXISTS memory_entries (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    memory_type TEXT NOT NULL CHECK (memory_type IN ('fact', 'preference', 'context', 'summary')),
    phone_number TEXT,
    conversation_id TEXT,
    importance_score REAL NOT NULL DEFAULT 1.0,
    access_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME,
    expires_at DATETIME,
    metadata TEXT DEFAULT '{}',  -- JSON
    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
);

-- User sessions table: Track user interaction sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    conversation_id TEXT NOT NULL,
    session_key TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    context_data TEXT DEFAULT '{}',  -- JSON
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);

-- Performance-critical indexes
-- Projects indexes
CREATE INDEX IF NOT EXISTS ix_projects_name ON projects (name);
CREATE INDEX IF NOT EXISTS ix_projects_vector_collection_name ON projects (vector_collection_name);
CREATE INDEX IF NOT EXISTS ix_projects_active_created ON projects (is_active, created_at);
CREATE INDEX IF NOT EXISTS ix_projects_created_at ON projects (created_at);

-- Conversations indexes
CREATE INDEX IF NOT EXISTS ix_conversations_project_id ON conversations (project_id);
CREATE INDEX IF NOT EXISTS ix_conversations_phone_number ON conversations (phone_number);
CREATE INDEX IF NOT EXISTS ix_conversations_session_id ON conversations (session_id);
CREATE INDEX IF NOT EXISTS ix_conversations_is_active ON conversations (is_active);
CREATE INDEX IF NOT EXISTS ix_conversations_last_activity ON conversations (last_activity);
CREATE INDEX IF NOT EXISTS ix_conversations_project_phone ON conversations (project_id, phone_number);
CREATE INDEX IF NOT EXISTS ix_conversations_active_activity ON conversations (is_active, last_activity);
CREATE INDEX IF NOT EXISTS ix_conversations_session_active ON conversations (session_id, is_active);

-- Messages indexes
CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS ix_messages_message_type ON messages (message_type);
CREATE INDEX IF NOT EXISTS ix_messages_whatsapp_message_id ON messages (whatsapp_message_id);
CREATE INDEX IF NOT EXISTS ix_messages_phone_number ON messages (phone_number);
CREATE INDEX IF NOT EXISTS ix_messages_processing_status ON messages (processing_status);
CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages (created_at);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_created ON messages (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS ix_messages_phone_created ON messages (phone_number, created_at);
CREATE INDEX IF NOT EXISTS ix_messages_type_status ON messages (message_type, processing_status);

-- Documents indexes
CREATE INDEX IF NOT EXISTS ix_documents_project_id ON documents (project_id);
CREATE INDEX IF NOT EXISTS ix_documents_filename ON documents (filename);
CREATE INDEX IF NOT EXISTS ix_documents_file_hash ON documents (file_hash);
CREATE INDEX IF NOT EXISTS ix_documents_processing_status ON documents (processing_status);
CREATE INDEX IF NOT EXISTS ix_documents_uploaded_at ON documents (uploaded_at);
CREATE INDEX IF NOT EXISTS ix_documents_project_status ON documents (project_id, processing_status);
CREATE INDEX IF NOT EXISTS ix_documents_filename_project ON documents (filename, project_id);

-- Document chunks indexes
CREATE INDEX IF NOT EXISTS ix_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS ix_document_chunks_chunk_index ON document_chunks (chunk_index);
CREATE INDEX IF NOT EXISTS ix_document_chunks_vector_id ON document_chunks (vector_id);
CREATE INDEX IF NOT EXISTS ix_chunks_document_index ON document_chunks (document_id, chunk_index);

-- Memory entries indexes
CREATE INDEX IF NOT EXISTS ix_memory_entries_project_id ON memory_entries (project_id);
CREATE INDEX IF NOT EXISTS ix_memory_entries_key ON memory_entries (key);
CREATE INDEX IF NOT EXISTS ix_memory_entries_memory_type ON memory_entries (memory_type);
CREATE INDEX IF NOT EXISTS ix_memory_entries_phone_number ON memory_entries (phone_number);
CREATE INDEX IF NOT EXISTS ix_memory_entries_conversation_id ON memory_entries (conversation_id);
CREATE INDEX IF NOT EXISTS ix_memory_entries_importance_score ON memory_entries (importance_score);
CREATE INDEX IF NOT EXISTS ix_memory_entries_created_at ON memory_entries (created_at);
CREATE INDEX IF NOT EXISTS ix_memory_entries_expires_at ON memory_entries (expires_at);
CREATE INDEX IF NOT EXISTS ix_memory_project_key ON memory_entries (project_id, key);
CREATE INDEX IF NOT EXISTS ix_memory_type_importance ON memory_entries (memory_type, importance_score);
CREATE INDEX IF NOT EXISTS ix_memory_phone_created ON memory_entries (phone_number, created_at);
CREATE INDEX IF NOT EXISTS ix_memory_expires ON memory_entries (expires_at);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS ix_user_sessions_conversation_id ON user_sessions (conversation_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_session_key ON user_sessions (session_key);
CREATE INDEX IF NOT EXISTS ix_user_sessions_phone_number ON user_sessions (phone_number);
CREATE INDEX IF NOT EXISTS ix_user_sessions_is_active ON user_sessions (is_active);
CREATE INDEX IF NOT EXISTS ix_user_sessions_started_at ON user_sessions (started_at);
CREATE INDEX IF NOT EXISTS ix_user_sessions_last_activity ON user_sessions (last_activity);
CREATE INDEX IF NOT EXISTS ix_sessions_phone_active ON user_sessions (phone_number, is_active);
CREATE INDEX IF NOT EXISTS ix_sessions_key_phone ON user_sessions (session_key, phone_number);
CREATE INDEX IF NOT EXISTS ix_sessions_activity ON user_sessions (last_activity);

-- Triggers for automatic timestamp updates
-- Projects updated_at trigger
CREATE TRIGGER IF NOT EXISTS tr_projects_updated_at
    AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Conversations updated_at and last_activity triggers
CREATE TRIGGER IF NOT EXISTS tr_conversations_updated_at
    AFTER UPDATE ON conversations
BEGIN
    UPDATE conversations 
    SET updated_at = CURRENT_TIMESTAMP,
        last_activity = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Messages trigger to update conversation last_activity
CREATE TRIGGER IF NOT EXISTS tr_messages_update_conversation_activity
    AFTER INSERT ON messages
BEGIN
    UPDATE conversations 
    SET last_activity = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
END;

-- Memory entries access tracking trigger
CREATE TRIGGER IF NOT EXISTS tr_memory_entries_access_update
    AFTER UPDATE ON memory_entries
    WHEN OLD.value != NEW.value OR OLD.importance_score != NEW.importance_score
BEGIN
    UPDATE memory_entries 
    SET last_accessed = CURRENT_TIMESTAMP,
        access_count = access_count + 1
    WHERE id = NEW.id;
END;

-- User sessions last_activity trigger
CREATE TRIGGER IF NOT EXISTS tr_user_sessions_activity_update
    AFTER UPDATE ON user_sessions
    WHEN OLD.context_data != NEW.context_data OR OLD.is_active != NEW.is_active
BEGIN
    UPDATE user_sessions 
    SET last_activity = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Session cleanup trigger (end sessions when conversation becomes inactive)
CREATE TRIGGER IF NOT EXISTS tr_conversations_end_sessions
    AFTER UPDATE ON conversations
    WHEN OLD.is_active = 1 AND NEW.is_active = 0
BEGIN
    UPDATE user_sessions 
    SET is_active = 0,
        ended_at = CURRENT_TIMESTAMP,
        last_activity = CURRENT_TIMESTAMP
    WHERE conversation_id = NEW.id AND is_active = 1;
END;

-- Insert initial data (optional default project)
-- INSERT OR IGNORE INTO projects (
--     id,
--     name,
--     description,
--     vector_collection_name,
--     settings
-- ) VALUES (
--     'default-project-id',
--     'Default Chatbot',
--     'Default WhatsApp AI Chatbot project',
--     'default_collection',
--     '{}'
-- );

-- Performance optimization views
-- Recent conversations view for quick access
CREATE VIEW IF NOT EXISTS v_recent_conversations AS
SELECT 
    c.*,
    p.name as project_name,
    COUNT(m.id) as message_count,
    MAX(m.created_at) as last_message_at
FROM conversations c
LEFT JOIN projects p ON c.project_id = p.id
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE c.is_active = 1
GROUP BY c.id
ORDER BY c.last_activity DESC;

-- Message statistics view
CREATE VIEW IF NOT EXISTS v_message_stats AS
SELECT 
    conversation_id,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN message_type = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN message_type = 'assistant' THEN 1 END) as assistant_messages,
    COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending_messages,
    AVG(tokens_used) as avg_tokens_used,
    MIN(created_at) as first_message_at,
    MAX(created_at) as last_message_at
FROM messages
GROUP BY conversation_id;

-- Document processing status view
CREATE VIEW IF NOT EXISTS v_document_status AS
SELECT 
    d.*,
    p.name as project_name,
    COUNT(dc.id) as actual_chunks_count
FROM documents d
LEFT JOIN projects p ON d.project_id = p.id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id;

-- Memory usage statistics view
CREATE VIEW IF NOT EXISTS v_memory_stats AS
SELECT 
    project_id,
    memory_type,
    COUNT(*) as entry_count,
    AVG(importance_score) as avg_importance,
    AVG(access_count) as avg_access_count,
    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at > CURRENT_TIMESTAMP THEN 1 END) as expiring_entries
FROM memory_entries
GROUP BY project_id, memory_type;

-- Database maintenance procedures (commented out - would be implemented in Python)
-- PRAGMA optimize;  -- Run periodically to update query planner statistics
-- VACUUM;  -- Run periodically to reclaim space
-- REINDEX;  -- Run if needed to rebuild indexes

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR REPLACE INTO schema_version (version, description) 
VALUES ('1.0.0', 'Initial schema with all core tables, indexes, and triggers');

-- Database integrity checks (can be run manually)
-- PRAGMA integrity_check;
-- PRAGMA foreign_key_check;