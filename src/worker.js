const { db, runMigrations } = require('./db');

async function pickAndRun() {
  // This is a minimal scheduler skeleton.
  // TODO: integrate with device gateway to instruct devices to download/apply firmware.
  const nowISO = new Date().toISOString();
  db.all(
    "SELECT * FROM rollouts WHERE status = 'scheduled' AND (scheduled_at IS NULL OR scheduled_at <= ?)",
    [nowISO],
    (err, rows) => {
      if (err) return console.error('Worker query error', err);
      rows.forEach((rollout) => {
        console.log(`Starting rollout id=${rollout.id} name=${rollout.name}`);
        // mark rollout running
        db.run("UPDATE rollouts SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE id = ?", [rollout.id]);
        // Fetch devices and log (in real integration, call gateway)
        db.all('SELECT device_id FROM rollout_devices WHERE rollout_id = ?', [rollout.id], (err2, devices) => {
          if (err2) return console.error('Error fetching devices for rollout', err2);
          devices.forEach((d) => {
            console.log(`Would instruct device ${d.device_id} to apply firmware ${rollout.firmware_path}`);
            // TODO: enqueue/notify device gateway and update rollout_devices status accordingly
          });
          // TODO: update rollout status to 'completed' when finished
        });
      });
    }
  );
}

async function startWorker() {
  await runMigrations();
  // Run once now, then every minute (configurable)
  pickAndRun();
  setInterval(pickAndRun, 60 * 1000);
}

if (require.main === module) {
  startWorker().catch((e) => {
    console.error('Worker failed', e);
    process.exit(1);
  });
}

module.exports = { pickAndRun, startWorker };
