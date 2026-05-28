export interface DeviceTelemetryMetric {
  id: number;
  deviceId: string;
  metricName: string;
  metricValue: number;
  timestamp: Date;
  createdAt: Date;
}

export interface CreateTelemetryRequest {
  deviceId: string;
  metricName: string;
  metricValue: number;
  timestamp?: Date;
}

export interface TelemetryQueryParams {
  deviceId: string;
  metricName?: string;
  startTime?: Date;
  endTime?: Date;
  limit?: number;
}
