from sqlalchemy.orm import Session
from typing import Any
import os
from datetime import datetime

from .client import airflow_client
from station.app.crud.crud_docker_trains import docker_train
from station.app.crud.crud_train_configs import docker_train_config
from station.app.schemas.docker_trains import DockerTrainConfig, DockerTrain, DockerTrainExecution


# TODO rework this !!!
def run_train(db: Session, train_id: Any, run_config: DockerTrainExecution):
    """
    Execute a PHT 1.0 docker train using a configured airflow instance

    :param db:
    :param train_id: identifier of the train
    :param run_config: given config_id or config_json can be used for running train
    :return:
    """

    if run_config.config_id != "default":
        config = docker_train_config.get(db, run_config.config_id)
    elif run_config.config_json:
        config = run_config.config_json
    else:
        print(f"Starting train {train_id} using default config")
        # Default config specifying only the identifier of the the train image and using the latest tag
        config = {
            "repository": f"{os.getenv('STATION_ID')}/{train_id}",
            "tag": "latest"
        }

    #  Execute the train using the airflow rest api
    run_id = airflow_client.trigger_dag("run_train", config=config)

    # Update the train state
    db_train = docker_train.get_by_train_id(db, train_id)
    db_train.is_active = True
    db_train.updated_at = datetime.now()
    if db_train.state:
        db_train.state.run_id = run_id
    db.commit()

    return run_id
