-- migration: add firmware_schedules table
CREATE TABLE IF NOT EXISTS firmware_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    targets TEXT NOT NULL,
    firmware_id TEXT NOT NULL,
    start_time DATETIME,
    rollout_window INTEGER DEFAULT 60,
    status TEXT DEFAULT 'scheduled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
