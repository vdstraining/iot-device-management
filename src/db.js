const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const defaultFile = path.join(__dirname, '..', 'data', 'rollouts.db');
const dbFile = process.env.DB_FILE || (process.env.NODE_ENV === 'test' ? ':memory:' : defaultFile);

const db = new sqlite3.Database(dbFile);

db.serialize(() => {
  db.run(
    `CREATE TABLE IF NOT EXISTS rollouts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      payload TEXT,
      state TEXT NOT NULL DEFAULT 'scheduled',
      due_at INTEGER NOT NULL,
      created_at INTEGER DEFAULT (strftime('%s','now'))
    );`
  );
});

module.exports = db;
