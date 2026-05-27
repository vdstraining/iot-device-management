-- migration: create firmware update jobs and targets tables

CREATE TABLE IF NOT EXISTS firmware_update_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  firmware_ref text NOT NULL,
  metadata jsonb,
  status text NOT NULL default 'pending',
  progress int NOT NULL default 0,
  scheduled_at timestamptz,
  created_by text,
  batch_size int,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS firmware_update_targets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES firmware_update_jobs(id) ON DELETE CASCADE,
  device_id text NOT NULL,
  status text NOT NULL default 'pending',
  attempts int NOT NULL default 0,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
