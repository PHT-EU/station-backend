from sqlalchemy.orm import Session
from typing import List, Union
import os

from station.clients.harbor_client import HarborClient
from station.app.crud import docker_train
from station.app.models.docker_trains import DockerTrain


def sync_db_with_registry(db: Session, station_id: Union[str, int] = None):
    """
    Sync the stations local docker train database with the harbor project associated with the station

    :param db: database handle
    :param station_id: Optional Parameter identifying the station, loads .env var "STATION_ID" if not given
    :return:
    """
    harbor_client = HarborClient()
    harbor_repos = harbor_client.get_artifacts_for_station(station_id)

    for repo in harbor_repos:
        train_id = repo["name"].split("/")[-1]
        docker_train.add_if_not_exists(db=db, train_id=train_id, created_at=repo["creation_time"])
