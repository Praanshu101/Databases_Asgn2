PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS member_group_map (
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    bio TEXT,
    skills TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_context (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    actor TEXT,
    request_id TEXT,
    session_token TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor TEXT,
    role TEXT,
    target_table TEXT,
    target_id INTEGER,
    details TEXT,
    status TEXT NOT NULL,
    request_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS db_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    row_id INTEGER,
    actor TEXT,
    request_id TEXT,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER IF NOT EXISTS trg_portfolios_insert
AFTER INSERT ON portfolios
BEGIN
    INSERT INTO db_change_log(table_name, operation, row_id, actor, request_id, source)
    VALUES(
        'portfolios',
        'INSERT',
        NEW.id,
        COALESCE((SELECT actor FROM audit_context WHERE id = 1), 'UNAUTHORIZED'),
        (SELECT request_id FROM audit_context WHERE id = 1),
        CASE WHEN (SELECT actor FROM audit_context WHERE id = 1) IS NULL THEN 'DIRECT_DB' ELSE 'API' END
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_portfolios_update
AFTER UPDATE ON portfolios
BEGIN
    INSERT INTO db_change_log(table_name, operation, row_id, actor, request_id, source)
    VALUES(
        'portfolios',
        'UPDATE',
        NEW.id,
        COALESCE((SELECT actor FROM audit_context WHERE id = 1), 'UNAUTHORIZED'),
        (SELECT request_id FROM audit_context WHERE id = 1),
        CASE WHEN (SELECT actor FROM audit_context WHERE id = 1) IS NULL THEN 'DIRECT_DB' ELSE 'API' END
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_portfolios_delete
AFTER DELETE ON portfolios
BEGIN
    INSERT INTO db_change_log(table_name, operation, row_id, actor, request_id, source)
    VALUES(
        'portfolios',
        'DELETE',
        OLD.id,
        COALESCE((SELECT actor FROM audit_context WHERE id = 1), 'UNAUTHORIZED'),
        (SELECT request_id FROM audit_context WHERE id = 1),
        CASE WHEN (SELECT actor FROM audit_context WHERE id = 1) IS NULL THEN 'DIRECT_DB' ELSE 'API' END
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_users_delete
AFTER DELETE ON users
BEGIN
    INSERT INTO db_change_log(table_name, operation, row_id, actor, request_id, source)
    VALUES(
        'users',
        'DELETE',
        OLD.id,
        COALESCE((SELECT actor FROM audit_context WHERE id = 1), 'UNAUTHORIZED'),
        (SELECT request_id FROM audit_context WHERE id = 1),
        CASE WHEN (SELECT actor FROM audit_context WHERE id = 1) IS NULL THEN 'DIRECT_DB' ELSE 'API' END
    );
END;
