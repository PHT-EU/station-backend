from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union, Any, Dict


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class DockerTrainState(DBSchema):
    num_executions: Optional[int] = 0
    status: Optional[str] = None
    last_execution: Optional[datetime] = None


class DockerTrainConfigBase(DBSchema):
    name: str
    airflow_config: Optional[Dict[str, Any]] = None
    cpu_requirements: Optional[Dict[str, Any]] = None
    gpu_requirements: Optional[Dict[str, Any]] = None
    auto_execute: Optional[bool] = None

class DockerTrainMinimal(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int
    is_active: bool
    train_id: Optional[str] = None

class DockerTrainConfig(DockerTrainConfigBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    trains: Optional[List[DockerTrainMinimal]] = None


class DockerTrainExecution(BaseModel):
    config_id: Optional[Union[int, str]] = "default"
    config_json: Optional[Dict[str, Any]] = None


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

class DockerTrainConfigCreate(DockerTrainConfigBase):
    train_id: Optional[Union[int, List[int]]] = None

class DockerTrainConfigUpdate(DockerTrainConfigBase):
    train_id: Optional[Union[int, List[int]]] = None