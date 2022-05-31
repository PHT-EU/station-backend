from datetime import datetime
from typing import Optional, Any
from enum import Enum

from pydantic import BaseModel


class StorageType(Enum):
    """
    Enum for storage types
    """
    LOCAL = "local"
    MINIO = "minio"
    DB = "db"


class DataType(Enum):
    """
    Enum for data types
    """
    IMAGE = "image"
    GENOME = "genome"
    FHIR = "fhir"
    CSV = "csv"
    STRUCTURED = "structured"
    UNSTRUCTURED = "unstructured"
    HYBRID = "hybrid"


class DataSetBase(BaseModel):
    name: str
    data_type: Optional[DataType] = None
    storage_type: Optional[StorageType] = None
    proposal_id: Optional[str] = None
    access_path: Optional[str] = None

    class Config:
        use_enum_values = True


class DataSetCreate(DataSetBase):
    pass


class DataSetUpdate(DataSetBase):
    pass


class DataSet(DataSetBase):
    id: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
