import { model } from './model';
import { DeviceTransport, defaultTransport } from './transport';

export async function processPendingJob(jobId: string, transport: DeviceTransport = defaultTransport) {
  const batch = await model.fetchPendingTargets(jobId, 10);
  for (const t of batch) {
    try {
      const r = await transport.sendFirmwareCommand(t.device_id, (await model.getJobById(jobId)).firmware_ref);
      if (r.ok) {
        await model.updateTargetStatus(t.id, 'succeeded', t.attempts + 1);
      } else {
        await model.updateTargetStatus(t.id, 'failed', t.attempts + 1, r.error);
      }
    } catch (e: any) {
      await model.updateTargetStatus(t.id, 'failed', t.attempts + 1, e.message || 'transport-error');
    }
  }
}

export default { processPendingJob };
