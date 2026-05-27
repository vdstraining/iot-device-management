export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface FirmwareJob {
  id: string;
  firmware_ref: string;
  metadata?: Record<string, any> | null;
  status: JobStatus;
  progress: number; // 0-100
  created_by?: string | null;
  scheduled_at?: string | null;
  batch_size?: number | null;
  created_at: string;
  updated_at: string;
}

export type TargetStatus = 'pending' | 'in_progress' | 'succeeded' | 'failed';

export interface FirmwareTarget {
  id: string;
  job_id: string;
  device_id: string;
  status: TargetStatus;
  attempts: number;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateFirmwareJobPayload {
  firmwareRef: string; // URL or blob id
  targets?: string[]; // explicit device IDs
  filter?: Record<string, any>; // alternative to targets
  batchSize?: number;
  scheduledAt?: string; // ISO datetime
  metadata?: Record<string, any>;
}
