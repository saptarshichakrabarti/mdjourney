-- Initial schema for the mdjourney authentication database.

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    email TEXT UNIQUE,
    full_name TEXT,
    disabled INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Global roles for users (e.g., admin, editor)
CREATE TABLE IF NOT EXISTS user_global_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(user_id, role)
);

-- Resource-specific roles for users (e.g., owner of a specific dataset)
CREATE TABLE IF NOT EXISTS user_resource_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resource_id TEXT NOT NULL,
    role TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE(user_id, resource_id, role)
);

-- Refresh tokens for persistent sessions
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_revoked INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- API keys for programmatic access
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    prefix TEXT UNIQUE NOT NULL,
    label TEXT,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_revoked INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Revoked token identifiers (TIDs) to support immediate logout
CREATE TABLE IF NOT EXISTS revoked_tids (
    tid TEXT PRIMARY KEY,
    revoked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Audit log index for tracking important events
CREATE TABLE IF NOT EXISTS audit_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    details TEXT,
    log_file_ref TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Triggers to update the 'updated_at' timestamp on user changes
CREATE TRIGGER IF NOT EXISTS update_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
