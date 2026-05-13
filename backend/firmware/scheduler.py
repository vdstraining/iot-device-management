from datetime import datetime
from .models import JOB_STORE, STATUS_RUNNING, STATUS_SUCCESS, STATUS_FAILED


def run_job(job_id: str):
    job = JOB_STORE.get(job_id)
    if not job:
        return
    if job.status in ("CANCELLED", "RUNNING", "SUCCESS", "FAILED"):
        return
    job.status = STATUS_RUNNING
    job.updated_at = datetime.utcnow()

    total = len(job.device_ids)
    failures = 0
    # process in batches
    for i in range(0, total, job.batch_size):
        batch = job.device_ids[i:i+job.batch_size]
        # simulate sending OTA commands and receiving results
        for device in batch:
            if device in job.failures_expected:
                job.per_device_status[device] = "FAILED"
                failures += 1
            else:
                job.per_device_status[device] = "SUCCESS"
        job.updated_at = datetime.utcnow()
        # check failure threshold
        if failures > job.failure_threshold:
            job.status = STATUS_FAILED
            job.updated_at = datetime.utcnow()
            return
    # decide success
    success_count = sum(1 for s in job.per_device_status.values() if s == "SUCCESS")
    if total == 0:
        job.status = STATUS_SUCCESS
    else:
        ratio = success_count / total
        if ratio >= 0.95:
            job.status = STATUS_SUCCESS
        else:
            job.status = STATUS_FAILED
    job.updated_at = datetime.utcnow()
