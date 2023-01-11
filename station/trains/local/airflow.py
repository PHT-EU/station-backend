from typing import Optional

from fhir_kindling.fhir_query.query_parameters import FHIRQueryParameters
from pydantic import BaseModel
from sqlalchemy.orm import Session

from station.app.crud.crud_datasets import datasets
from station.app.crud.crud_local_train import local_train
from station.app.crud.crud_train_configs import docker_train_config
from station.app.crud.local_train_master_image import local_train_master_image
from station.app.schemas.local_trains import LocalTrainExecution
from station.clients.airflow.client import airflow_client
from station.clients.airflow.docker_trains import process_dataset, process_db_config


class FHIRConfig(BaseModel):
    server_id: str
    query_string: Optional[str] = None
    parameters: Optional[FHIRQueryParameters] = None


class AirflowRunConfig(BaseModel):
    train_id: str
    env: Optional[dict] = None
    volumes: Optional[dict] = None
    master_image: Optional[str] = None
    custom_image: Optional[str] = None
    fhir: Optional[FHIRConfig] = None


def run_local_train(db: Session, train_id: str, dataset_id: str = None, config_id: int = None) -> LocalTrainExecution:
    """
    Run a local train

    :param train_id: id of the train
    :param dataset_id: optional id of the dataset
    :param config_id: optional id of the config
    :return: config dictionary
    """
    db_train = local_train.get(db, train_id)
    if db_train is None:
        raise ValueError(f"Train {train_id} not found")
    config = make_dag_config(db, db_train, train_id, dataset_id, config_id)
    print(config)
    run_id = airflow_client.trigger_dag("run_local_train", config=config)
    train_execution = local_train.create_run(
        db,
        train_id=train_id,
        dag_run=run_id,
        config_id=config_id,
        dataset_id=dataset_id
    )

    return train_execution


def make_dag_config(db: Session, db_train, train_id: str, dataset_id: str = None, config_id: int = None) -> dict:
    """
    Create a config dictionary for the airflow DAG

    :param train_id: id of the train
    :param dataset_id: optional id of the dataset
    :param config_id: optional id of the config
    :return: config dictionary
    """

    if db_train.master_image_id:
        master_image = local_train_master_image.get(db, db_train.master_image_id).image_id
    else:
        master_image = None

    dag_config = {
        "train_id": train_id,
        "master_image": master_image,
        "custom_image": db_train.custom_image
    }

    if dataset_id:
        ds = datasets.get(db, dataset_id)
        process_dataset(dag_config, ds)
    if config_id:
        db_config = docker_train_config.get(db, config_id)
        process_db_config(dag_config, db_config)

    return dag_config
