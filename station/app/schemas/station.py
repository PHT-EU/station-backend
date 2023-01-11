from typing import List, Optional

from pydantic import BaseModel

from station.app.schemas.docker_trains import DockerTrain
from station.app.schemas.trains import Train


class Trains(BaseModel):
    docker_trains: Optional[List[DockerTrain]]
    federated_trains: Optional[List[Train]]

    class Config:
        orm_mode = True


class TrainOverViewResponse(BaseModel):
    active: Optional[Trains] = None
    available: Optional[Trains] = None
