from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Any
import os
from datetime import datetime
import json

from .client import airflow_client
from station.app.crud.crud_docker_trains import docker_trains
from station.app.crud.crud_train_configs import docker_train_config
from station.app.schemas.docker_trains import DockerTrainExecution, DockerTrainSavedExecution, DockerTrainAirflowConfig, DockerTrainState
from station.app.models.docker_trains import DockerTrainState as dtsmodel, DockerTrainExecution as dtemodel


def update_state(db, db_train, run_time) -> DockerTrainState:
    """
    Update the train state object corresponding to the train
    :param db: database session
    :param db_train: train object
    :param run_time: time when run is triggered
    :return: train state object
    """
    trainstate = db.query(dtsmodel).filter(dtsmodel.train_id == db_train.id).first()
    if trainstate:
        trainstate.last_execution = run_time
        trainstate.num_executions += 1
        trainstate.status = 'active'
    else:
        print("No train state assigned.")
    db.add(trainstate)
    db.commit()
    db.refresh(trainstate)

    return trainstate


def validate_run_config(db: Session, train_id: Any, execution_params: DockerTrainExecution) -> DockerTrainAirflowConfig:
    """
    Validate the config used for the triggered run
    :param db: database session
    :param train_id: train id of the train to run
    :param execution_params: includes the config_id of the config to use or the specified config
    :return:
    """
    # Extract config by id if given
    if execution_params.config_id != "default":
        config_general = docker_train_config.get(db, execution_params.config_id)
        try:
            config = config_general.airflow_config
        except:
            raise HTTPException(status_code=400, detail="No airflow config given by this id.")
    # Extract config as defined in the execution
    elif execution_params.config_json:
        config = json.loads(execution_params.config_json.json())
    # Using the default config
    else:
        print(f"Starting train {train_id} using default config")
        # Default config specifies only the identifier of the the train image and uses the latest tag
        config = {
            "repository": f"{os.getenv('HARBOR_BASE_URL')}/station_{os.getenv('STATION_ID')}/{train_id}",
            "tag": "latest"
        }

    if config["repository"] is None or config["tag"] is None:
        raise HTTPException(status_code=400, detail="Train run parameters are missing.")

    return config


def update_train(db, db_train, run_id):
    """
    Update train parameters
    :param db: database session
    :param db_train: db_train object to update
    :param run_id: run_id of the triggered run
    :return:
    """
    db_train.is_active = True
    run_time = datetime.now()
    db_train.updated_at = run_time

    # Update the train state
    trainstate = update_state(db, db_train, run_time)

    # Create an execution
    execution = dtemodel(train_id=db_train.id, airflow_dag_run=run_id)
    db.add(execution)
    db.commit()
    db.refresh(execution)

    db.commit()

    return db_train

def run_train(db: Session, train_id: Any, execution_params: DockerTrainExecution) -> DockerTrainSavedExecution:
    """
    Execute a PHT 1.0 docker train using a configured airflow instance

    :param db: database session
    :param train_id: identifier of the train
    :param execution_params: given config_id or config_json can be used for running train
    :return:
    """
    # Use default config if there is no config defined.
    if execution_params is None:
        execution_params = DockerTrainExecution(config_id="default")
        print("No config defined. Default config is used.")

    config = validate_run_config(db, train_id, execution_params)

    # Extract the train from the database
    db_train = docker_trains.get_by_train_id(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Train with id '{train_id}' not found.")

    # Execute the train using the airflow rest api
    try:
        run_id = airflow_client.trigger_dag("run_pht_train", config=config)
        db_train = update_train(db, db_train, run_id)
    except:
        raise HTTPException(status_code=503, detail="No connection to the airflow client could be established.")

    try:
        last_execution = db_train.executions[-1]
    except:
        last_execution = None
        print("No executions registered.")

    return last_execution
