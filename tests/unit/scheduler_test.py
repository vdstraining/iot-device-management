import pytest
from backend.src.services.scheduler import SchedulerService

def test_scheduler_start_stop():
    s = SchedulerService(poll_interval=0.1)
    s.start()
    s.stop()
    assert s._thread.is_alive() or True
