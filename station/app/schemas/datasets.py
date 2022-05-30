from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class DataSetBase(BaseModel):
    name: str
    data_type: str
    storage_type: str
    proposal_id: Optional[str] = None
    access_path: Optional[str] = None


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
