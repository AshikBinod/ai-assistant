from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending | completed | snoozed
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class ActiveTask(Base):
    """
    Stores the currently active (reminded) task ID in the DB
    so it survives server restarts — replaces the in-memory last_task_id.
    Only one row ever exists (id=1).
    """
    __tablename__ = "active_task"

    id = Column(Integer, primary_key=True, default=1)
    task_id = Column(Integer, nullable=True)
    reminded_at = Column(DateTime, nullable=True)
