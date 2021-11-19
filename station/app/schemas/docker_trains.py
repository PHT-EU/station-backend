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


class AirflowEnvironmentVariable(BaseModel):
    key: str
    value: str


class DockerVolume(BaseModel):
    host_path: str
    container_path: str
    mode: Optional[str] = "ro"


class AirflowConfig(BaseModel):
    env: Optional[List[AirflowEnvironmentVariable]] = None
    volumes: Optional[List[DockerVolume]] = None


class DockerTrainConfigBase(DBSchema):
    name: str
    airflow_config: Optional[AirflowConfig] = None
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
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    trains: Optional[List[DockerTrainMinimal]] = None


class DockerTrainConfigMinimal(DockerTrainConfigBase):
    created_at: datetime
    updated_at: Optional[datetime] = None


class DockerRunVolume(BaseModel):
    pass


class DockerTrainExecution(BaseModel):
    config_id: Optional[Union[int, str]] = "default"
    config_json: Optional[Dict[str, Any]] = None
    repository: Optional[str] = None
    tag: Optional[str] = None
    volumes: Optional[List[DockerRunVolume]] = None


class DockerTrain(DBSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int
    is_active: bool
    train_id: Optional[str] = None
    config_id: Optional[int] = None
    config: Optional[DockerTrainConfigMinimal] = None
    state: Optional[DockerTrainState] = None


class DockerTrainConfigCreate(DockerTrainConfigBase):
    pass


class DockerTrainConfigUpdate(DockerTrainConfigBase):
    pass


class DockerTrainCreate(BaseModel):
    train_id: str
    proposal_id: Optional[int] = None
    config: Optional[DockerTrainConfigCreate] = None
    config_name: Optional[str] = None
    config_id: Optional[int] = None


class DockerTrainUpdate(DockerTrainCreate):
    pass
