from pydantic import BaseModel
from typing import List, Optional

from station.app.schemas.trains import Train
from station.app.schemas.docker_trains import DockerTrain


class Trains(BaseModel):
    docker_trains: Optional[List[DockerTrain]]
    federated_trains: Optional[List[Train]]

    class Config:
        orm_mode = True


class TrainOverViewResponse(BaseModel):
    active: Optional[Trains] = None
    available: Optional[Trains] = None


class ServiceStatus(BaseModel):
    name: str
    status: str


class DiskUsage(BaseModel):
    total: int
    used: int
    free: int
    percent: float


class HardwareResources(BaseModel):
    cpu: float
    memory: float
    disk: DiskUsage
    gpu: Optional[float] = None


class StationStatus(BaseModel):
    services: List[ServiceStatus]
    hardware: HardwareResources
    docker: str
