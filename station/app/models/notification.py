from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, Float, BigInteger
from sqlalchemy.orm import relationship, deferred
from datetime import datetime

from station.app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    target_user = Column(String, default="all")
    topic = Column(String, default="trains")
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
