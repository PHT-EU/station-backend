from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

import uuid

from datetime import datetime

from station.app.db.base_class import Base


class DataSet(Base):
    __tablename__ = "datasets"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    proposal_id = Column(String, nullable=True)
    name = Column(String)
    data_type = Column(String, nullable=True)
    storage_type = Column(String, nullable=True)
    access_path = Column(String, nullable=True)
    fhir_server = Column(Integer, ForeignKey('fhir_servers.id'), nullable=True)
    summary = Column(JSON, nullable=True)
    # trains = relationship("Train", back_populates="dataset")
