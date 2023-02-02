from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from station.app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    target_user = Column(String, default="all")
    topic = Column(String, default="trains")
    title = Column(String, nullable=True)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    type = Column(String, default="info")
    created_at = Column(DateTime, default=datetime.now())
