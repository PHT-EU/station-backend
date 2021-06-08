from sqlalchemy.orm import Session
from typing import Any
import os
from datetime import datetime

from .client import airflow_client
from station.app.crud.docker_trains import read_train_by_train_id
from station.app.schemas.docker_trains import DockerTrainRun, DockerTrain



def run_train(db: Session, train_id: Any, run_config: DockerTrainRun):
    """
    Execute a PHT 1.0 docker train using a configured airflow instance

    :param db:
    :param train_id: identifier of the train
    :param config_id: id of a stored run configuration if none is given default config is used
    :return:
    """

    if run_config.config_id != "default":
        # TODO get config
        pass
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
    db_train = read_train_by_train_id(db, train_id)
    db_train.is_active = True
    db_train.updated_at = datetime.now()
    db_train.last_execution = run_id
    db.commit()

    return run_id





