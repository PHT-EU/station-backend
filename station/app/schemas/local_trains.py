import uuid

from pydantic import BaseModel, root_validator
from datetime import datetime
from typing import Optional, Dict


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class LocalTrainMasterImageBase(BaseModel):
    registry: Optional[str] = None
    group: Optional[str] = None
    artifact: Optional[str] = None
    tag: Optional[str] = "latest"
    image_id: Optional[str] = None

    @root_validator
    def image_specified(cls, values):
        image_id = values.get("image_id")
        if not image_id:
            registry, group, artifact = values.get("registry"), values.get("group"), values.get("artifact")
            if not registry or not group or not artifact:
                raise ValueError("Image ID or registry, group and artifact must be specified.")
        return values


class LocalTrainMasterImageCreate(LocalTrainMasterImageBase):
    pass


class LocalTrainMasterImageUpdate(LocalTrainMasterImageBase):
    pass


class LocalTrainMasterImage(LocalTrainMasterImageBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


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
