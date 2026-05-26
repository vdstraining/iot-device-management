const express = require('express');
const db = require('./db');

const app = express();
app.use(express.json());

app.post('/rollouts', (req, res) => {
  const { payload, due_at } = req.body;
  if (!due_at) return res.status(400).json({ error: 'due_at required' });

  const dueTs = Math.floor(new Date(due_at).getTime() / 1000);
  const sql = 'INSERT INTO rollouts (payload, due_at, state) VALUES (?, ?, "scheduled")';
  db.run(sql, [JSON.stringify(payload || null), dueTs], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    db.get('SELECT * FROM rollouts WHERE id = ?', [this.lastID], (e, row) => {
      if (e) return res.status(500).json({ error: e.message });
      res.status(201).json(row);
    });
  });
});

app.get('/rollouts/:id', (req, res) => {
  db.get('SELECT * FROM rollouts WHERE id = ?', [req.params.id], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'not found' });
    res.json(row);
  });
});

app.patch('/rollouts/:id/pause', (req, res) => {
  db.run('UPDATE rollouts SET state = ? WHERE id = ?', ['paused', req.params.id], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    if (this.changes === 0) return res.status(404).json({ error: 'not found' });
    db.get('SELECT * FROM rollouts WHERE id = ?', [req.params.id], (e, row) => {
      if (e) return res.status(500).json({ error: e.message });
      res.json(row);
    });
  });
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log('Server listening on', port));
}

module.exports = app;
