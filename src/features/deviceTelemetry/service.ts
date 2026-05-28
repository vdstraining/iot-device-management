import { DeviceTelemetryModel } from './model';
import { CreateTelemetryRequest, DeviceTelemetryMetric, TelemetryQueryParams } from './types';

export class DeviceTelemetryService {
  async recordMetric(request: CreateTelemetryRequest): Promise<DeviceTelemetryMetric> {
    if (!request.deviceId) {
      throw new Error('deviceId is required');
    }
    if (!request.metricName) {
      throw new Error('metricName is required');
    }
    if (request.metricValue === undefined || request.metricValue === null) {
      throw new Error('metricValue is required');
    }

    return DeviceTelemetryModel.create(request);
  }

  async queryMetrics(params: TelemetryQueryParams): Promise<DeviceTelemetryMetric[]> {
    if (!params.deviceId) {
      throw new Error('deviceId is required for query');
    }

    if (params.metricName) {
      return DeviceTelemetryModel.findByMetricName(params.metricName);
    }

    return DeviceTelemetryModel.findByDeviceId(params.deviceId, params.limit);
  }
}
