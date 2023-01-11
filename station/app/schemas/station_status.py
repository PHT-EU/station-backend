from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class HealthStatus(str, Enum):
    healthy = 'healthy'
    stopped = 'stopped'
    error = 'error'


class StatusDocker(BaseModel):
    Id: str


class ServiceStatus(BaseModel):
    name: str
    status: HealthStatus


class DiskUsage(BaseModel):
    total: int
    used: int
    free: int
    percent: float


class MemoryUsage(BaseModel):
    total: int
    available: int
    free: int
    used: int
    percent: float


class HardwareResources(BaseModel):
    cpu: List[float]
    memory: MemoryUsage
    disk: DiskUsage
    gpu: Optional[float] = None


class StationStatus(BaseModel):
    services: List[ServiceStatus]
    hardware: HardwareResources
    docker: Optional[dict] = None
