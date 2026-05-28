CREATE TABLE device_telemetry (
  id SERIAL PRIMARY KEY,
  device_id VARCHAR(255) NOT NULL,
  metric_name VARCHAR(255) NOT NULL,
  metric_value FLOAT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_device FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE INDEX idx_device_telemetry_device_id ON device_telemetry(device_id);
CREATE INDEX idx_device_telemetry_metric_name ON device_telemetry(metric_name);
CREATE INDEX idx_device_telemetry_timestamp ON device_telemetry(timestamp);
