from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON

from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from station.app.db.base_class import Base


class StorageType(Enum):
    """
    Enum for storage types
    """
    LOCAL = 1
    MINIO = 2
    DB = 3


class DataType(Enum):
    """
    Enum for data types
    """
    IMAGE = 1
    GENOME = 2
    FHIR = 3
    CSV = 4
    STRUCTURED = 5
    UNSTRUCTURED = 6
    HYBRID = 7


class DataSet(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, nullable=True)
    proposal_id = Column(Integer, nullable=True)
    name = Column(String)
    data_type = Column(SQLAEnum(DataType), default=DataType.IMAGE)
    storage_type = Column(SQLAEnum(StorageType), default=StorageType.MINIO)
    access_path = Column(String, nullable=True)
    fhir_server = Column(Integer, ForeignKey('fhir_servers.id'), nullable=True)
    summary = Column(JSON, nullable=True)
    # trains = relationship("Train", back_populates="dataset")
