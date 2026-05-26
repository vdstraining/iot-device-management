from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FirmwareSchedule(Base):
    __tablename__ = 'firmware_schedules'
    id = Column(Integer, primary_key=True)
    targets = Column(Text)
    firmware_id = Column(String(256))
    start_time = Column(DateTime)
    rollout_window = Column(Integer)
    status = Column(String(32), default='scheduled')
    created_at = Column(DateTime, default=datetime.utcnow)
