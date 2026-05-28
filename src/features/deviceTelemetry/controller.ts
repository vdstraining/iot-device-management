import { DeviceTelemetryService } from './service';
import { CreateTelemetryRequest } from './types';

export class DeviceTelemetryController {
  private service = new DeviceTelemetryService();

  async postMetric(req: any, res: any): Promise<void> {
    try {
      const payload: CreateTelemetryRequest = {
        deviceId: req.body.deviceId,
        metricName: req.body.metricName,
        metricValue: req.body.metricValue,
        timestamp: req.body.timestamp ? new Date(req.body.timestamp) : undefined,
      };

      const result = await this.service.recordMetric(payload);
      res.status(201).json(result);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  }

  async getMetrics(req: any, res: any): Promise<void> {
    try {
      const params = {
        deviceId: req.query.deviceId,
        metricName: req.query.metricName,
        limit: req.query.limit ? parseInt(req.query.limit) : 100,
      };

      const results = await this.service.queryMetrics(params);
      res.status(200).json(results);
    } catch (error: any) {
      res.status(400).json({ error: error.message });
    }
  }
}
