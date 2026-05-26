CREATE TABLE IF NOT EXISTS rollouts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payload TEXT,
  state TEXT NOT NULL DEFAULT 'scheduled',
  due_at INTEGER NOT NULL,
  created_at INTEGER DEFAULT (strftime('%s','now'))
);
