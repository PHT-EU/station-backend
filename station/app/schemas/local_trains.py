from pydantic import BaseModel, root_validator
from datetime import datetime
from typing import Optional, Dict


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class LocalTrainMasterImage(BaseModel):
    group: str
    artifact: str
    tag: Optional[str] = "latest"
    image_id: Optional[str] = None


class LocalTrainBase(BaseModel):
    name: str
    TrainID: int


class LocalTrainRun(BaseModel):
    train_id: str
    run_id: str


class LocalTrainCreate(BaseModel):
    train_name: str


class LocalTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    train_id: Optional[str] = None
    config_id: Optional[int] = None


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
