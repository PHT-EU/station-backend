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
    run_id: Optional[str] = None


class DockerTrainConfigBase(DBSchema):
    name: str
    airflow_config_json: Optional[Dict[str, Any]] = None
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


class DockerTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int
    is_active: bool
    train_id: Optional[str] = None
    config_id: Optional[int] = None
    config: Optional[DockerTrainConfigBase] = None
    state: Optional[DockerTrainState] = None


class DockerTrainConfigCreate(DockerTrainConfigBase):
    pass


class DockerTrainConfigUpdate(DockerTrainConfigBase):
    pass

class DockerTrainCreate(BaseModel):
    train_id: str
    proposal_id: Optional[int] = None
    config: Optional[DockerTrainConfigCreate] = None
    config_id: Optional[int] = None

class DockerTrainUpdate(DockerTrainCreate):
    pass
