from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class LocalTrainBase(BaseModel):
    train_id: str
    train_name: str


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


class LocalTrainConfigSchema(BaseModel):
    name: str
    image: str
    tag: Optional[str] = None
    query: Optional[str] = None
    entrypoint: str
    volumes: Optional[str] = None
    env: Optional[str] = None
    train_id: Optional[str] = None


class LocalTrainAirflowConfigSchema(BaseModel):
    repository: Optional[str] = None
    tag: Optional[str] = None
    env: Optional[str] = None
    query: Optional[str] = None
    entrypoint: Optional[str] = None
    volumes: Optional[str] = None
    train_id: Optional[str] = None


class LocalTrainSchema(BaseModel):
    id: str
    train_id: str
    train_name: str
    config_id:  Optional[str]
    airflow_config_json: Optional[LocalTrainAirflowConfigSchema]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool


class LocalTrainSchemaList(BaseModel):
    trains: list[LocalTrainSchema]


class LocalTrainAirflowConfigSchemas(BaseModel):
    configs: list[LocalTrainAirflowConfigSchema]


class LocalTrainAddMasterImage(BaseModel):
    train_id: str
    image: str


class LocalTrainGetFile(BaseModel):
    train_id: str
    file_name: str


class LocalTrainFile(BaseModel):
    file: str


class LocalTrainAddTag(BaseModel):
    train_id: str
    tag: str


class LocalTrainAddQuery(BaseModel):
    train_id: str
    query: str


class LocalTrainAddEntrypoint(BaseModel):
    train_id: str
    entrypoint: str


class MinIOFile(BaseModel):
    bucket_name: str
    object_name: str
    last_modified: datetime
    size: str


class AllFilesTrain(BaseModel):
    files: list[MinIOFile]

class MasterImagesList(BaseModel):
    images: list[str]

class LocalTrainUpdate(LocalTrainCreate):
    pass


class LocalTrainUploadTrainFileResponse(BaseModel):
    train_id: str
    filename: str


class LocalTrainLog(BaseModel):
    run_id: str
    log: Optional[str]
