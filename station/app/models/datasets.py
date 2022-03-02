from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
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
    fhir_user = Column(String, default=None)
    fhir_password = Column(String, default=None)
    fhir_server_type = Column(String, default=None)
    n_items = Column(Integer, default=0)
    target_field = Column(String, default=None)
    class_distribution = Column(String, default=None)
    #trains = relationship("Train", back_populates="dataset")
    trains = Column(Integer, default=0)
