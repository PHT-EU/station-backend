from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union, Any


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class DockerTrainState(DBSchema):
    num_executions: int
    status: str
    last_execution: Optional[datetime] = None


class DockerTrainConfigBase(DBSchema):
    name: str
    airflow_config: Optional[dict[str, Any]] = None
    cpu_requirements: Optional[dict[str, Any]] = None
    gpu_requirements: Optional[dict[str, Any]] = None
    auto_execute: Optional[bool] = None


class DockerTrainConfigCreate(DockerTrainConfigBase):
    pass


class DockerTrainConfigUpdate(DockerTrainConfigBase):
    pass


class DockerTrainConfig(DockerTrainConfigBase):
    created_at: datetime
    updated_at: Optional[datetime] = None


class DockerTrainExecution(BaseModel):
    config_id: Optional[Union[int, str]] = "default"
    config_json: Optional[dict] = None


class DockerTrainCreate(BaseModel):
    train_id: str
    proposal_id: Optional[int] = None
    config_id: Optional[int] = None
    config_name: Optional[str] = None


class DockerTrainUpdate(DockerTrainCreate):
    pass


class DockerTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int
    is_active: bool
    train_id: Optional[str] = None
    config: Optional[DockerTrainConfig] = None
    state: Optional[DockerTrainState] = None