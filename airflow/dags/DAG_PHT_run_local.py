import asyncio
import io
import sys
import tarfile
from datetime import timedelta
import json
import os
from io import BytesIO
from pathlib import Path
import shutil
import ast

import docker
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.utils.dates import days_ago
from docker.errors import APIError
from train_lib.train.build_test_train import build_test_train
from train_lib.clients import PHTFhirClient
from train_lib.security import SecurityProtocol
from cryptography.hazmat.primitives.serialization import load_pem_private_key
# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

from station.app.models.local_trains import LocalTrain
from fastapi import Depends
from station.app.api import dependencies
from sqlalchemy.orm import Session

from train_lib.docker_util.docker_ops import extract_train_config, extract_query_json
from train_lib.security.SecurityProtocol import SecurityProtocol
from train_lib.clients import PHTFhirClient

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
from station.clients.minio import MinioClient

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
}


@dag(default_args=default_args, schedule_interval=None, start_date=days_ago(2), tags=['pht', 'train'])
def run_local():
    """
    Defins a DAG simular to the run train only for local execution of test Trains dosent contain any of the sequrety
    and stores the restults not ecripted into the minIO.
    @return:
    """
    @task()
    def get_train_configuration() -> dict:
        """
        extra the train state dict form airflow context

        @return: train_state_dict
        """
        context = get_current_context()
        repository, tag, env, entrypoint, volumes ,query ,train_id, run_id = [context['dag_run'].conf.get(_, None) for _ in
                                                    ['repository', 'tag', 'env', 'entrypoint', 'volumes', 'query', 'train_id', 'run_id']]
        img = repository + ":" + tag
        train_state_dict = {
            "repository": repository,
            "train_id": train_id,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes,
            "query": query,
            "entrypoint": entrypoint,
            "build_dir": "./temp/",
            "bucket_name": "localtrain",
            "run_id" : context['dag_run'].run_id
        }
        return train_state_dict

    @task()
    def pull_docker_image(train_state_dict)-> dict:
        """
        pull the master Image from harbor

        @param train_state_dict:
        @return: train_state_dict
        """
        docker_client = docker.from_env()
        harbor_address = os.getenv("HARBOR_API_URL")
        docker_client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                            registry=harbor_address)
        docker_client.images.pull(repository=train_state_dict["repository"], tag=train_state_dict["tag"])

        images = docker_client.images.list()
        return train_state_dict

    @task()
    def build_train(train_state_dict)-> dict:
        """
        Build the train by extracting the entrypoint from minIO and adding it to the pulled image

        @param train_state_dict:
        @return:
        """
        # create minIO client
        docker_client = docker.from_env()
        minio_client = MinioClient(minio_server="minio:9000")

        # create temp folder for saving files from minIO and results.
        Path(train_state_dict["build_dir"]).mkdir(parents=True, exist_ok=True)

        # create the docker File like object that can be added to the master image
        docker_file = f'''
                            FROM {train_state_dict["img"]}
                            RUN mkdir /opt/pht_results
                            RUN mkdir /opt/pht_train
                            RUN chmod -R +x /opt/pht_train
                            CMD ["python", "/opt/pht_train/entrypoint.py"]
                            '''
        docker_file = BytesIO(docker_file.encode("utf-8"))

        # create docker container
        image, logs = docker_client.images.build(fileobj=docker_file)
        container = docker_client.containers.create(image.id)

        # load teh endpoint form minIO into to a local tar file
        endpoint = minio_client.get_file(train_state_dict["bucket_name"], f"{train_state_dict['train_id']}/{train_state_dict['entrypoint']}")
        name = "entrypoint.py"
        tarfile_name = f"{train_state_dict['build_dir']}/{name}.tar"
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name='entrypoint.py')
            data_file.size = len(endpoint)
            tar.addfile(data_file, io.BytesIO(endpoint))

        # add teh endpoint tar file to the train container in /opt/pht_train
        with open(tarfile_name, 'rb') as fd:
            respons = container.put_archive("/opt/pht_train", fd)
            container.wait()
        container.commit(repository="local_train", tag="latest")
        container.wait()

        return train_state_dict

    @task()
    def execute_query(train_state_dict)-> dict:
        """
        if a query is defind in the train parameters, the query file is loaded  and executed in the same way
        as the normal trains.
        the query results are saved localy into the AIRFLOW_DATA_DIR if exists(if not "/opt/station_data")
        The train_state_dict gets updateted with the enviroment variabls and the volume information for the data folder

        @param dict train_state_dict: train parameters
        @return: dict train_state_dict: train parameters
        """
        # check if a query is defind
        if train_state_dict["query"] is None:
            return train_state_dict
        #try to cache errors and save to logs
        try:
            # start the FHIR client
            fhir_url = os.getenv("FHIR_ADDRESS", None)
            fhir_user = os.getenv("FHIR_USER", None)
            fhir_pw = os.getenv("FHIR_PW", None)
            fhir_token = os.getenv("FHIR_TOKEN", None)
            fhir_server_type = os.getenv("FHIR_SERVER_TYPE", None)

            fhir_client = PHTFhirClient(
                server_url=fhir_url,
                username=fhir_user,
                password=fhir_pw,
                token=fhir_token,
                fhir_server_type=fhir_server_type,
                disable_k_anon=True
            )
            loop = asyncio.get_event_loop()

            # load the query
            minio_client = MinioClient(minio_server="minio:9000")
            query_string = minio_client.get_file(train_state_dict["bucket_name"],
                                             f"{train_state_dict['train_id']}/{train_state_dict['query']}").decode("utf-8")
            query = ast.literal_eval(query_string)

            # execute the query
            query_result = loop.run_until_complete(fhir_client.execute_query(query=query))
            output_file_name = query["data"]["filename"]

            # Create the file path in which to store the FHIR query results
            data_dir = os.getenv("AIRFLOW_DATA_DIR", "/opt/station_data")

            train_data_dir = os.path.join(data_dir, train_state_dict["train_id"])
            Path(train_data_dir).mkdir(parents=True, exist_ok=True)

            train_data_dir = os.path.abspath(train_data_dir)
            train_data_path = fhir_client.store_query_results(query_result, storage_dir=train_data_dir,
                                                              filename=output_file_name)


            host_data_path = os.path.join(os.getenv("STATION_DATA_DIR"), train_state_dict["train_id"], output_file_name)

            # add the informaiton to the train parameters
            query_data_volume = {
                host_data_path: {
                    "bind": f"/opt/train_data/{output_file_name}",
                    "mode": "ro"
                }
            }
            data_dir_env = {
                "TRAIN_DATA_PATH": f"/opt/train_data/{output_file_name}"
            }

            if isinstance(train_state_dict.get("volumes"), dict):
                train_state_dict["volumes"] = {**query_data_volume, **train_state_dict["volumes"]}
            else:
                train_state_dict["volumes"] = query_data_volume

            if train_state_dict.get("env", None):
                train_state_dict["env"] = {**train_state_dict["env"], **data_dir_env}
            else:
                train_state_dict["env"] = data_dir_env
        except Exception as e:
            # save logs for errors that happend during query execution
            with open(f'{train_state_dict["build_dir"]}log.txt', 'a+') as f:
                f.write(e)

        return train_state_dict

    @task()
    def run_train(train_state_dict)-> dict:
        """
        The container gets executetd with the enviroment varibals and volumes
        whait

        @param dict train_state_dict: train parameters
        @return: dict train_state_dict: train parameters
        """
        docker_client = docker.from_env()

        environment = train_state_dict.get("env", {})
        volumes = train_state_dict.get("volumes", {})
        container = docker_client.containers.run("local_train", environment=environment, volumes=volumes,
                                                 detach=True)
        container.wait()
        with open(f'{train_state_dict["build_dir"]}results.tar', 'wb')  as f:
            bits, stat = container.get_archive('opt/pht_results')
            for chunk in bits:
                f.write(chunk)

        with open(f'{train_state_dict["build_dir"]}log.txt', 'a+')  as f:
            logs = container.logs().decode("utf-8")
            f.write(logs)
        container.remove(v=True, force=True)
        return train_state_dict

    @task()
    def save_results(train_state_dict)-> dict:
        """
        Stores the results and logs form the container inot minIO

        @param dict train_state_dict: train parameters
        @return: dict train_state_dict: train parameters
        """
        minio_client = MinioClient(minio_server="minio:9000")
        #Store results
        with open(f'{train_state_dict["build_dir"]}results.tar', 'rb') as results_tar:
            asyncio.run(
                minio_client.store_files(bucket=train_state_dict["bucket_name"], name=f"{train_state_dict['train_id']}/results.tar", file=results_tar))
        #Store logs
        with open(f'{train_state_dict["build_dir"]}log.txt', 'rb') as logs:
            asyncio.run(
                minio_client.store_files(bucket=train_state_dict["bucket_name"],
                                         name=f"{train_state_dict['train_id']}/{train_state_dict['run_id']}/log.", file=logs))

        return train_state_dict

    @task()
    def clean_up(train_state_dict):
        """
        Remove all tempory data form the build dir

        @param dict train_state_dict: train parameters
        @return:
        """
        try:
            shutil.rmtree(str(train_state_dict["build_dir"]))
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

        #TODO add the removeing or storage of query results
    local_train = get_train_configuration()
    local_train = pull_docker_image(local_train)
    local_train = build_train(local_train)
    local_train = execute_query(local_train)
    local_train = run_train(local_train)
    local_train = save_results(local_train)
    clean_up(local_train)

run_local = run_local()
