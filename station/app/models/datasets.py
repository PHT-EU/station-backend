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
    access_path = Column(String, nullable=True)
    fhir_server_id = Column(Integer, nullable=True)
    target_field = Column(String, nullable=True)
