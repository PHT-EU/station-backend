from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union, Any, Dict


class DBSchema(BaseModel):
    class Config:
        orm_mode = True


class DockerTrainState(DBSchema):
    num_executions: Optional[int] = 0
    status: Optional[str] = "inactive"
    last_execution: Optional[datetime] = None


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


class DockerTrainAirflowConfig(AirflowConfig):
    repository: Optional[str] = None
    tag: Optional[str] = None


class DockerTrainConfigBase(DBSchema):
    name: str
    airflow_config: Optional[DockerTrainAirflowConfig] = None
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


class DockerTrainExecution(DBSchema):
    config_id: Optional[Union[int, str]] = "default"
    config_json: Optional[DockerTrainAirflowConfig] = None


class DockerTrainSavedExecution(DBSchema):
    start: datetime
    end: Optional[datetime] = None
    airflow_dag_run : Optional[str] = None


class DockerTrain(DBSchema):
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    proposal_id: int = 0
    is_active: bool = False
    train_id: Optional[str] = None
    config_id: Optional[int] = None
    config: Optional[DockerTrainConfigMinimal] = None
    state: Optional[DockerTrainState] = None
    executions: Optional[List[DockerTrainSavedExecution]] = None


class DockerTrainConfigCreate(DockerTrainConfigBase):
    pass


class DockerTrainConfigUpdate(DockerTrainConfigBase):
    pass


class DockerTrainCreate(BaseModel):
    train_id: str
    proposal_id: Optional[int] = None
    config: Optional[Union[DockerTrainConfigCreate, int]] = None


class DockerTrainUpdate(DockerTrainCreate):
    pass
