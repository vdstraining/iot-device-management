# SCRUM-147: Add Device Telemetry Endpoint

## Requirement Summary

The system requires a device telemetry collection and querying feature to enable:
- Devices to report time-series metrics (temperature, humidity, battery level, etc.)
- Users to retrieve and analyze historical telemetry data
- Background worker processes to aggregate and clean up old metrics

## Business Goal

Enable real-time and historical telemetry tracking for IoT devices with API endpoints for metric recording and queries.

## Scope

### In Scope
- REST endpoints for metric recording (POST /api/telemetry/metrics)
- REST endpoints for metric querying (GET /api/telemetry/metrics)
- Database schema for telemetry storage
- Service layer with validation and error handling
- Unit tests for core functionality
- Background worker skeleton for aggregation and cleanup

### Out of Scope
- Message queue integration (defer to SCRUM-148)
- Real-time streaming/WebSocket support
- Advanced analytics and reporting UI
- High-cardinality metric support

## Acceptance Criteria

1. Users can POST a metric to /api/telemetry/metrics with deviceId, metricName, and metricValue
2. Users can GET metrics from /api/telemetry/metrics with optional filters (deviceId, metricName, limit)
3. All required fields are validated; missing fields return 400 Bad Request
4. Metrics include id, timestamp, and createdAt fields
5. Unit tests verify happy path and error scenarios
6. Database migration creates device_telemetry table with appropriate indexes

## Constraints

- Must follow existing MVC architecture patterns from SCRUM-146
- API responses must be JSON
- Timestamps should be ISO 8601 format
- Performance acceptable for datasets < 10M records per device

## Edge Cases

- Device ID not found in devices table
- Invalid metric values (NaN, Infinity)
- Concurrent metric writes from same device
- Query results > 100K records

## Risks

- Database migration timing critical for production deployment
- Performance may degrade with high-cardinality metrics without proper indexing
- Message queue integration deferred; could cause bottleneck

## Questions

1. What is the retention policy for telemetry data?
2. Should we support custom metric types beyond the initial set?
3. Is real-time aggregation required or can it be batch processed?
