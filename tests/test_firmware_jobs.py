import sys
import os
import json
# ensure repo root on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.firmware.api import app
from backend.firmware.models import JOB_STORE, FirmwareUpdateJob
from backend.firmware.scheduler import run_job
from datetime import datetime, timedelta


def test_create_and_get_job():
    client = app.test_client()
    data = {
        "firmware_version": "1.2.3",
        "device_ids": ["dev1", "dev2", "dev3"],
        "batch_size": 2,
        "failure_threshold": 1,
        "schedule_time": datetime.utcnow().isoformat()
    }
    rv = client.post('/api/firmware-jobs', json=data)
    assert rv.status_code == 201
    job = rv.get_json()
    jid = job['id']
    # get
    rv2 = client.get(f'/api/firmware-jobs/{jid}')
    assert rv2.status_code == 200
    got = rv2.get_json()
    assert got['firmware_version'] == '1.2.3'


def test_cancel_job():
    client = app.test_client()
    data = {"firmware_version": "2.0.0", "device_ids": ["a","b"]}
    rv = client.post('/api/firmware-jobs', json=data)
    assert rv.status_code == 201
    job = rv.get_json()
    jid = job['id']
    rv2 = client.patch(f'/api/firmware-jobs/{jid}/cancel')
    assert rv2.status_code == 200
    got = rv2.get_json()
    assert got['status'] == 'CANCELLED'


def test_scheduler_run_success_and_failure():
    # create job with one expected failure
    client = app.test_client()
    data = {
        "firmware_version": "3.0.0",
        "device_ids": ["d1","d2","d3","d4","d5"],
        "batch_size": 2,
        "failure_threshold": 1,
        "failures_expected": ["d2"]
    }
    rv = client.post('/api/firmware-jobs', json=data)
    assert rv.status_code == 201
    job = rv.get_json()
    jid = job['id']
    # run job synchronously
    run_job(jid)
    j = JOB_STORE[jid]
    assert j.status in ("SUCCESS", "FAILED")
    # since 4/5 success -> 80% <95% -> FAILED
    assert j.status == 'FAILED'
    # now create mostly successful job
    data2 = {
        "firmware_version": "3.0.1",
        "device_ids": ["x1","x2","x3","x4","x5","x6","x7","x8","x9","x10","x11","x12","x13","x14","x15","x16","x17","x18","x19","x20"],
        "batch_size": 3,
        "failure_threshold": 2,
        "failures_expected": ["x10"]
    }
    rv = client.post('/api/firmware-jobs', json=data2)
    assert rv.status_code == 201
    job2 = rv.get_json()
    jid2 = job2['id']
    run_job(jid2)
    j2 = JOB_STORE[jid2]
    assert j2.status == 'SUCCESS'
