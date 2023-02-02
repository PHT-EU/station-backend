import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, root_validator


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
            registry, group, artifact = (
                values.get("registry"),
                values.get("group"),
                values.get("artifact"),
            )
            if not registry or not group or not artifact:
                raise ValueError(
                    "Image ID or registry, group and artifact must be specified."
                )
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


class LocalTrainConfigurationStep(str, Enum):
    initialized = "initialized"
    image_configured = "image_configured"
    files_uploaded = "files_uploaded"
    dataset_selected = "dataset_selected"
    train_configured = "train_configured"
    finished = "finished"


class LocalTrainStateBase(BaseModel):
    last_execution: Optional[datetime] = None
    num_executions: int = 0
    status: str = "inactive"
    configuration_state: LocalTrainConfigurationStep = None

    class Config:
        use_enum_values = True


class LocalTrainStateCreate(LocalTrainStateBase):
    pass


class LocalTrainStateUpdate(LocalTrainStateBase):
    pass


class LocalTrainState(LocalTrainStateBase):
    id: int

    class Config:
        orm_mode = True


class LocalTrainExecution(BaseModel):
    id: uuid.UUID
    train_id: uuid.UUID
    airflow_dag_run: Optional[str] = None
    config_id: Optional[int] = None
    dataset_id: Optional[uuid.UUID] = None
    start: datetime
    finish: Optional[datetime] = None

    class Config:
        orm_mode = True


class LocalTrainBase(BaseModel):
    name: Optional[str] = None
    master_image_id: Optional[Any] = None
    entrypoint: Optional[str] = None
    files: Optional[List[str]] = None
    custom_image: Optional[str] = None
    fhir_query: Optional[Union[str, dict]] = None
    command: Optional[str] = None
    command_args: Optional[str] = None


class LocalTrainCreate(LocalTrainBase):
    pass


class LocalTrainUpdate(LocalTrainBase):
    pass


class LocalTrain(LocalTrainBase, DBSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: Optional[str] = None
    state: Optional[LocalTrainState] = None


class LocalTrainRunConfig(BaseModel):
    dataset_id: Optional[str] = None
    config_id: Optional[int] = None
    config: Optional[Dict] = None
