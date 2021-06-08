from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class DockerTrainCreate(BaseModel):
    train_id: str
    proposal_id: Optional[int] = None
    config_id: Optional[int] = None
    config_name: Optional[str] = None


class DockerTrainUpdate(DockerTrainCreate):
    pass


class DockerTrainRun(BaseModel):
    config_id: Optional[Union[int, str]] = "default"
    config_json: Optional[dict] = None


class DockerTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int
    is_active: bool
    train_id: Optional[str] = None
    last_execution: Optional[str] = None
