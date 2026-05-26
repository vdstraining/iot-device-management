# Rollouts MVP (SCRUM-56) — quick run

Run the DB migration (creates local sqlite DB by default):

```bash
npm install
npm run migrate
```

Start the API server:

```bash
npm start
# server listens on http://localhost:3000
```

Run the scheduler worker (skeleton that logs actions):

```bash
npm run worker
```

Run tests:

```bash
npm test
```

Notes:
- Migration SQL is in `migrations/V1__create_rollouts.sql`.
- API endpoints:
  - `POST /rollouts` -> create rollout. Body: `{ name, firmware_path, scheduled_at?, device_ids? }`
  - `GET /rollouts/{id}` -> get rollout with devices
  - `PATCH /rollouts/{id}/pause` -> pause rollout
- DB: By default uses `data.db` in repo root. Set `DB_FILE` env var to use a different sqlite file.
- TODO: add RBAC (middleware) and integrate `src/worker.js` with device gateway to notify devices.
