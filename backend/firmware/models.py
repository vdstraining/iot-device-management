from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid

STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED"

@dataclass
class FirmwareUpdateJob:
    id: str
    firmware_version: str
    target_group_id: Optional[str]
    device_ids: List[str]
    schedule_time: datetime
    batch_size: int
    status: str
    failure_threshold: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    failures_expected: List[str] = field(default_factory=list)
    per_device_status: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "firmware_version": self.firmware_version,
            "target_group_id": self.target_group_id,
            "device_ids": self.device_ids,
            "schedule_time": self.schedule_time.isoformat(),
            "batch_size": self.batch_size,
            "status": self.status,
            "failure_threshold": self.failure_threshold,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "failures_expected": self.failures_expected,
            "per_device_status": self.per_device_status,
        }

    @staticmethod
    def from_dict(data: dict):
        sid = data.get("id") or str(uuid.uuid4())
        schedule_time = data.get("schedule_time")
        if isinstance(schedule_time, str):
            schedule_time = datetime.fromisoformat(schedule_time)
        now = datetime.utcnow()
        device_ids = data.get("device_ids") or []
        return FirmwareUpdateJob(
            id=sid,
            firmware_version=data.get("firmware_version"),
            target_group_id=data.get("target_group_id"),
            device_ids=device_ids,
            schedule_time=schedule_time or now,
            batch_size=int(data.get("batch_size", 1)),
            status=data.get("status", STATUS_PENDING),
            failure_threshold=int(data.get("failure_threshold", 1)),
            created_by=data.get("created_by"),
            created_at=now,
            updated_at=now,
            failures_expected=data.get("failures_expected") or [],
            per_device_status={d: "PENDING" for d in device_ids},
        )


# Simple in-memory job store
JOB_STORE: Dict[str, FirmwareUpdateJob] = {}
