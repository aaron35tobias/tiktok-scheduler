from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from models.base import Base

class ScheduledPost(Base):
    __tablename__ = 'scheduled_posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, nullable=False)
    caption = Column(String, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="Pending", nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ScheduledPost(id={self.id}, status='{self.status}', scheduled_time='{self.scheduled_time}')>"
