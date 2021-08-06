from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, LargeBinary, Float, BigInteger
from sqlalchemy.orm import relationship, deferred
from datetime import datetime

from station.app.db.base_class import Base


class DataSet(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    proposal_id = Column(Integer, default=0)
    name = Column(String)
    data_type = Column(String, default="image")
    storage_type = Column(String, default="minio")
    access_path = Column(String, nullable=True)
    n_items = Column(Integer, default=0)
    trains = relationship("Train", back_populates="dataset")

