from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union, Dict, Any


class DataSetBase(BaseModel):
    name: str
    data_type: str
    storage_type: str
    proposal_id: Optional[Any]
    # TODO improve clarity of access definition
    access_path: Optional[str]
    n_items: Optional[int]


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
