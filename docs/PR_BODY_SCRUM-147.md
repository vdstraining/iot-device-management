## Jira
- SCRUM-147

## Requirement Summary
- Add device telemetry collection and querying endpoints to the IoT device management system, allowing devices to report metrics and users to retrieve historical telemetry data.

## Implementation Summary
- Added Device Telemetry feature module under \src/features/deviceTelemetry\ with complete MVC architecture (model, controller, service, types, worker, transport).
- Created database migration for \device_telemetry\ table with device_id, metric_name, metric_value, and timestamp fields.
- Implemented REST endpoints: POST /api/telemetry/metrics (record) and GET /api/telemetry/metrics (query).
- Added comprehensive unit tests for service layer validation and error handling.

## Changed Areas
- Added \db/migrations/20260528_create_device_telemetry.sql\
- Added \src/features/deviceTelemetry/\ module with model, controller, service, types, worker, transport
- Added \src/features/deviceTelemetry/__tests__/service.test.ts\

## Testing Summary
- Unit tests: Passing (service validation, error handling)
- Integration tests: Ready for implementation
- Simulation tests: Not included in this PR

## Risks / Follow-ups
- Database migration requires coordination with deployment process
- Background worker queue integration pending infrastructure setup
- Metric aggregation and retention policies to be defined

## Reviewer Notes
- This PR adds telemetry recording and query endpoints following existing patterns from SCRUM-146.
- Mock implementations included; database connection to be configured during integration phase.
