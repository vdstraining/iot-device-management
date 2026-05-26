# Firmware updates

This document describes the minimal firmware schedule feature implemented for SCRUM-106.

Usage:
- POST /api/firmware/schedules with JSON {targets, firmware_id, start_time, rollout_window}

Rollback:
- Currently minimal: operator can cancel schedules (TODO: implement cancel endpoint).

Testing:
- Unit and integration tests under `tests/` run with `pytest`.

TODOs:
- Persist per-device results and audit logs
- Implement cancel endpoint, staged rollouts, firmware host auth
