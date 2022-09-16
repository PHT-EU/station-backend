from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime

from station.app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    target_user = Column(String, default="all")
    topic = Column(String, default="trains")
    title = Column(String, nullable=True)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
