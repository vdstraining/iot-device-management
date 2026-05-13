from flask import Flask, request, jsonify, abort
from datetime import datetime
from .models import FirmwareUpdateJob, JOB_STORE, STATUS_CANCELLED

app = Flask(__name__)

@app.route('/api/firmware-jobs', methods=['POST'])
def create_job():
    data = request.get_json() or {}
    if not data.get('firmware_version'):
        return jsonify({"error": "firmware_version required"}), 400
    device_ids = data.get('device_ids') or []
    # allow schedule_time as ISO string
    schedule_time = data.get('schedule_time')
    job = FirmwareUpdateJob.from_dict({
        'firmware_version': data.get('firmware_version'),
        'target_group_id': data.get('target_group_id'),
        'device_ids': device_ids,
        'schedule_time': schedule_time,
        'batch_size': data.get('batch_size', 1),
        'failure_threshold': data.get('failure_threshold', 1),
        'created_by': data.get('created_by'),
        'failures_expected': data.get('failures_expected', []),
    })
    JOB_STORE[job.id] = job
    return jsonify(job.to_dict()), 201

@app.route('/api/firmware-jobs', methods=['GET'])
def list_jobs():
    return jsonify([j.to_dict() for j in JOB_STORE.values()])

@app.route('/api/firmware-jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    job = JOB_STORE.get(job_id)
    if not job:
        abort(404)
    return jsonify(job.to_dict())

@app.route('/api/firmware-jobs/<job_id>/cancel', methods=['PATCH'])
def cancel_job(job_id):
    job = JOB_STORE.get(job_id)
    if not job:
        abort(404)
    job.status = STATUS_CANCELLED
    job.updated_at = datetime.utcnow()
    return jsonify(job.to_dict())

# helper to run scheduler manually via API for testing/demo
@app.route('/api/firmware-jobs/<job_id>/run', methods=['POST'])
def run_job_now(job_id):
    from .scheduler import run_job
    job = JOB_STORE.get(job_id)
    if not job:
        abort(404)
    run_job(job_id)
    return jsonify(job.to_dict())

if __name__ == '__main__':
    app.run(debug=True)
