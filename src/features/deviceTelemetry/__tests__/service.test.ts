import { DeviceTelemetryService } from '../service';
import { CreateTelemetryRequest } from '../types';

describe('DeviceTelemetryService', () => {
  let service: DeviceTelemetryService;

  beforeEach(() => {
    service = new DeviceTelemetryService();
  });

  test('should record a metric with valid data', async () => {
    const request: CreateTelemetryRequest = {
      deviceId: 'device-001',
      metricName: 'temperature',
      metricValue: 25.5,
    };

    const result = await service.recordMetric(request);
    expect(result.deviceId).toBe('device-001');
    expect(result.metricName).toBe('temperature');
    expect(result.metricValue).toBe(25.5);
    expect(result.id).toBeDefined();
  });

  test('should throw error when deviceId is missing', async () => {
    const request: any = {
      metricName: 'temperature',
      metricValue: 25.5,
    };

    await expect(service.recordMetric(request)).rejects.toThrow('deviceId is required');
  });

  test('should throw error when metricValue is missing', async () => {
    const request: any = {
      deviceId: 'device-001',
      metricName: 'temperature',
    };

    await expect(service.recordMetric(request)).rejects.toThrow('metricValue is required');
  });
});
