from pydantic import BaseModel
from datetime import datetime
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
