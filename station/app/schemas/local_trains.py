from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class LocalTrainBase(BaseModel):
    name: str
    TrainID: int


class LocalTrainRun(BaseModel):
    train_id: str
    run_id: str


class LocalTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    train_id: Optional[str] = None
    config_id: Optional[int] = None


class LocalTrainCreate(BaseModel):
    train_name: Optional[str] = None


class LocalTrainConfig(BaseModel):
    name: str
    image: str
    tag: Optional[str]
    query: Optional[str]
    entrypoint: str
    volumes: Optional[str]
    train_id: Optional[str]


class LocalTrainAddMasterImage(BaseModel):
    train_id: str
    image: str


class LocalTrainGetFile(BaseModel):
    train_id: str
    file_name: str


class LocalTrainAddTag(BaseModel):
    train_id: str
    tag: str


class LocalTrainGetFile(BaseModel):
    train_id: str
    file_name: str


class LocalTrainUpdate(LocalTrainCreate):
    pass
