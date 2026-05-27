import { FirmwareJob, FirmwareTarget } from './types';
import { v4 as uuidv4 } from 'uuid';

const jobs: Record<string, FirmwareJob> = {};
const targets: Record<string, FirmwareTarget> = {};

export const model = {
  async createJob(job: Partial<FirmwareJob>) {
    const id = uuidv4();
    const now = new Date().toISOString();
    const created: FirmwareJob = {
      id,
      firmware_ref: job.firmware_ref || '',
      metadata: job.metadata || null,
      status: job.status || 'pending',
      progress: job.progress || 0,
      created_by: job.created_by || null,
      scheduled_at: job.scheduled_at || null,
      batch_size: job.batch_size || null,
      created_at: now,
      updated_at: now
    };
    jobs[id] = created;
    return created;
  },

  async createTargetsBulk(jobId: string, deviceIds: string[]) {
    const created: FirmwareTarget[] = [];
    const now = new Date().toISOString();
    for (const d of deviceIds) {
      const id = uuidv4();
      const t: FirmwareTarget = {
        id,
        job_id: jobId,
        device_id: d,
        status: 'pending',
        attempts: 0,
        last_error: null,
        created_at: now,
        updated_at: now
      };
      targets[id] = t;
      created.push(t);
    }
    return created;
  },

  async getJobById(jobId: string) {
    return jobs[jobId];
  },

  async getTargetsByJobId(jobId: string, limit = 100, offset = 0) {
    return Object.values(targets).filter(t => t.job_id === jobId).slice(offset, offset + limit);
  },

  async fetchPendingTargets(jobId: string, batchSize = 10) {
    return Object.values(targets).filter(t => t.job_id === jobId && t.status === 'pending').slice(0, batchSize);
  },

  async updateTargetStatus(targetId: string, status: string, attempts = 0, lastError?: string) {
    const t = targets[targetId];
    if (!t) return null;
    t.status = status as any;
    t.attempts = attempts;
    t.last_error = lastError || null;
    t.updated_at = new Date().toISOString();
    return t;
  },

  async updateJobProgress(jobId: string, progress: number, status?: string) {
    const j = jobs[jobId];
    if (!j) return null;
    j.progress = progress;
    if (status) j.status = status as any;
    j.updated_at = new Date().toISOString();
    return j;
  }
};
