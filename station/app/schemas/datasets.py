from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union, Dict, Any


class DataSetBase(BaseModel):
    name: str
    data_type: str
    storage_type: str
    # TODO in models DataSet proposal_id is a integer -> desiding if what it has to be at the ende
    proposal_id: Optional[int] = None
    # proposal_id: Optional[Any]
    # TODO improve clarity of access definition
    access_path: Optional[str]
    n_items: Optional[int]


class DataSetCreate(DataSetBase):
    target_field: Optional[str]
    fhir_user: Optional[str]
    fhir_password: Optional[str]
    fhir_server_type: Optional[str]


class DataSetUpdate(DataSetBase):
    pass


class DataSet(DataSetBase):
    id: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
