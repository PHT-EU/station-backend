from typing import List, Optional

from pydantic import BaseModel


class StationKeys(BaseModel):
    station_id: int
    signing_key: str
    sharing_key: str
    key_signature: Optional[str] = None

    class Config:
        orm_mode = True


class BroadCastKeysSchema(BaseModel):
    train_id: int
    iteration: int
    keys: List[StationKeys]


class GetCyphersRequest(BaseModel):
    station_id: int
    iteration: int
