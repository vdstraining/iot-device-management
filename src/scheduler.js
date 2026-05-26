const db = require('./db');

function processDue() {
  const now = Math.floor(Date.now() / 1000);
  db.all('SELECT * FROM rollouts WHERE state = ? AND due_at <= ?', ['scheduled', now], (err, rows) => {
    if (err) return console.error('Scheduler error:', err.message);
    rows.forEach((row) => {
      db.run('UPDATE rollouts SET state = ? WHERE id = ?', ['processing', row.id], function (e) {
        if (e) return console.error('Scheduler update error:', e.message);
        console.log('Processing rollout', row.id);
        // Simulate action and mark completed
        db.run('UPDATE rollouts SET state = ? WHERE id = ?', ['completed', row.id], (ee) => {
          if (ee) return console.error('Scheduler complete error:', ee.message);
          console.log('Completed rollout', row.id);
        });
      });
    });
  });
}

if (require.main === module) {
  console.log('Scheduler started');
  setInterval(processDue, 1000);
}

module.exports = { processDue };
