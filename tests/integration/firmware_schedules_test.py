from fastapi.testclient import TestClient
from backend.src.app import app
import json

client = TestClient(app)

def test_create_schedule():
    payload = {
        "targets": ["device1","device2"],
        "firmware_id": "fw-1",
        "start_time": "2030-01-01T00:00:00Z",
        "rollout_window": 30
    }
    r = client.post('/api/firmware/schedules', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['firmware_id'] == 'fw-1'
