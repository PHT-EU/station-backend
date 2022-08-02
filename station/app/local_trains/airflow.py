from sqlalchemy.orm import Session

from station.app.crud.crud_local_train import local_train
from station.app.crud.local_train_master_image import local_train_master_image
from station.app.crud.crud_datasets import datasets
from station.app.crud.crud_train_configs import docker_train_config

from station.app.config import settings
from station.clients.airflow.docker_trains import process_dataset, process_db_config
from station.clients.airflow.client import airflow_client


def run_local_train(db: Session, train_id: str, dataset_id: str = None, config_id: int = None) -> dict:
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
    run_id = airflow_client.trigger_dag("run_local_train", config=config)
    return config


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
