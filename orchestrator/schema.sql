-- TAD AI Orchestrator Worker Tracking Schema
-- SQLite database for tracking sub-agent workers

CREATE TABLE workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_name TEXT UNIQUE NOT NULL,
    session_key TEXT UNIQUE,
    status TEXT DEFAULT 'idle', -- idle, running, completed, failed, cancelled
    task_type TEXT, -- coding, testing, blockchain, analysis
    task_description TEXT,
    project_path TEXT,
    progress INTEGER DEFAULT 0, -- 0-100
    eta_minutes INTEGER,
    model_provider TEXT DEFAULT 'kimi',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_output TEXT, -- Last 500 chars of output
    error_message TEXT,
    cost_usd REAL DEFAULT 0.0
);

CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    task_type TEXT,
    description TEXT,
    status TEXT,
    duration_seconds INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES workers(id)
);

CREATE TABLE orchestrator_state (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize with max workers setting
INSERT INTO orchestrator_state (key, value) VALUES ('max_workers', '3');
INSERT INTO orchestrator_state (key, value) VALUES ('active_workers', '0');
INSERT INTO orchestrator_state (key, value) VALUES ('total_tasks_completed', '0');
