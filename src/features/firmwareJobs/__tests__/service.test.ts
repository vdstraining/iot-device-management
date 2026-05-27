import { model } from '../model';
import { FirmwareUpdateService } from '../service';
import { defaultTransport } from '../transport';

test('service creates job and targets', async () => {
  const svc = new FirmwareUpdateService({ model, transport: defaultTransport });
  const payload = { firmwareRef: 'http://example.com/fw.bin', targets: ['dev1','dev2'] };
  const job = await svc.createFirmwareJob(payload, 'tester');
  expect(job).toBeDefined();
  const targets = await model.getTargetsByJobId(job.id);
  expect(targets.length).toBe(2);
});
