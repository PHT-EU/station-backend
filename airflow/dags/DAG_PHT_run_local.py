import sys
import os
import os.path

import docker
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.hooks.base import BaseHook

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from docker.errors import APIError

from airflow.utils.dates import days_ago

from station.app.models.local_trains import LocalTrain
from station.app.models.docker_trains import DockerTrainConfig
from station.app.models.datasets import DataSet
from station.app.trains.local.build import build_train
from station.clients.minio import MinioClient

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    # 'retries': 1,
    # 'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}


@dag(default_args=default_args, schedule_interval=None, start_date=days_ago(2), tags=['pht', 'local train'])
def run_local_train():
    @task()
    def get_local_train_config():
        context = get_current_context()
        train_id, env, volumes, master_image, custom_image = [context['dag_run'].conf.get(_, None) for _ in
                                  ['train_id', 'env', 'volumes', 'master_image', 'custom_image']]



        # check and process the volumes passed to the dag via the config
        if volumes:
            assert isinstance(volumes, dict)
            # if a volume in the dictionary follows the docker format pass it as is

            for key, item in volumes.items():
                # check if docker volume keys are present and raise an error if not
                if isinstance(item, dict):
                    if not ("bind" in item and "mode" in item):
                        raise ValueError("Incorrectly formatted docker volume, 'bind' and 'mode' keys are required")
                # transform simple path:path volumes into correctly formatted docker read only volumes
                elif isinstance(item, str):
                    volumes[key] = {
                        "bind": item,
                        "mode": "ro"
                    }

        train_config = {
            "train_id": train_id,
            "env": env,
            "volumes": volumes
        }

        return train_config

    @task()
    def build_train_image(train_config):

        connection = BaseHook.get_connection("pg_station")

        db_url = f"postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/" \
                 f"{connection.schema}"

        # create a session to the station database
        engine = create_engine(db_url)
        train_id = train_config['train_id']
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session_local()


        # get the train files from minio
        minio_client = MinioClient(
            minio_server=os.getenv("MINIO_SERVER"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
        )

        train_files_archive = minio_client.get_local_train_archive(train_id)

        image = build_train(
            db=db,
            train_id=train_id,
            custom_image=train_config.get('custom_image'),
            master_image_id=train_config.get('master_image'),
            files=train_files_archive,
        )

        train_config['image'] = image

        db.close()
        return train_config

    def run_train(train_config):
        env = train_config['env']
        volumes = train_config['volumes']

    train_config = get_local_train_config()
    train_config = build_train_image(train_config)
    run_train(train_config)


local_train_dag = run_local_train()
