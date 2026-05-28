import { DeviceTelemetryController } from './controller';

export class DeviceTelemetryTransport {
  private controller = new DeviceTelemetryController();

  setupRoutes(app: any): void {
    app.post('/api/telemetry/metrics', (req: any, res: any) => this.controller.postMetric(req, res));
    app.get('/api/telemetry/metrics', (req: any, res: any) => this.controller.getMetrics(req, res));
  }
}
