import { Request, Response } from 'express';
import { model } from './model';
import { defaultTransport } from './transport';
import { FirmwareUpdateService } from './service';

const service = new FirmwareUpdateService({ model, transport: defaultTransport });

export const createFirmwareJob = async (req: Request, res: Response) => {
  try {
    const payload = req.body;
    if (!payload || !payload.firmwareRef) {
      return res.status(400).json({ error: 'firmwareRef is required' });
    }
    const job = await service.createFirmwareJob(payload, (req as any).user?.id || null);
    return res.status(201).json({ job });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || 'internal' });
  }
};
