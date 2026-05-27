import { CreateFirmwareJobPayload } from './types';
import { DeviceTransport } from './transport';

export class FirmwareUpdateService {
  model: any;
  transport: DeviceTransport;

  constructor(opts: { model: any; transport: DeviceTransport }) {
    this.model = opts.model;
    this.transport = opts.transport;
  }

  async createFirmwareJob(payload: CreateFirmwareJobPayload, createdBy?: string) {
    if (!payload || !payload.firmwareRef) throw new Error('firmwareRef required');
    const job = await this.model.createJob({ firmware_ref: payload.firmwareRef, metadata: payload.metadata || null, status: 'pending', progress: 0, created_by: createdBy || null, batch_size: payload.batchSize || null, scheduled_at: payload.scheduledAt || null });
    const deviceIds = payload.targets || [];
    await this.model.createTargetsBulk(job.id, deviceIds);
    // In a real app enqueue job id for background processing. Here we return job.
    return job;
  }
}
