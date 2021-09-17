from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from station.app.schemas import protocol
from station.app.schemas import datasets


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class TrainState(DBSchema):
    id: int
    iteration: int
    round: int
    updated_at: Optional[datetime] = None
    signing_key: Optional[str] = None
    sharing_key: Optional[str] = None
    seed: Optional[int] = None
    key_broadcast: Optional[str] = None


class TrainCreate(BaseModel):
    name: Optional[str] = None
    proposal_id: Optional[str] = None


class TrainUpdate(TrainCreate):
    pass


class Train(DBSchema):
    id: int
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    proposal_id: Optional[str] = None
    state: TrainState
    token: Optional[str] = None
    dataset: Optional[datasets.DataSet] = None
