import asyncio
import io
import sys
import tarfile
from datetime import timedelta
import json
import os
from io import BytesIO

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
def run_aachen_pht_train():
    @task()
    def get_train_configuration():
        context = get_current_context()
        dockerfile, endpoint, requirements, dockerignore, bucket, build_dir, environment = [
            context['dag_run'].conf.get(_, None) for _ in
            ['dockerfile', 'endpoint', 'requirements', 'dockerignore', 'bucket', 'build_dir', 'environment']]

        build_dir = "./temp/"
        results = "./result/"
        repo = f'aachen_{endpoint.lower()}_train'
        print(repo)
        train_state_dict = {
            "dockerfile": dockerfile,
            "endpoint": endpoint,
            "requirements": requirements,
            "dockerignore": dockerignore,
            "bucket": bucket,
            "build_dir": build_dir,
            "results": results,
            "repo": repo,
            "environment": environment
        }
        return train_state_dict

    @task()
    def build_image(train_state_dict):
        # clients
        docker_client = docker.from_env()
        minio_client = MinioClient(minio_server="minio:9000")

        # load the requierd files from min io and save them into minio
        if not os.path.exists(train_state_dict["build_dir"]):
            os.makedirs(train_state_dict["build_dir"])

        requirements_file = minio_client.get_file(train_state_dict["bucket"],
                                                  train_state_dict["requirements"])
        requirements_file = BytesIO(requirements_file)

        with open(train_state_dict["build_dir"] + train_state_dict["requirements"], 'wb') as f:
            f.write(requirements_file.getbuffer())

        dockerignore_file = minio_client.get_file(train_state_dict["bucket"],
                                                  train_state_dict["dockerignore"])
        dockerignore_file = BytesIO(dockerignore_file)
        with open(train_state_dict["build_dir"] + train_state_dict["dockerignore"], 'wb') as f:
            f.write(dockerignore_file.getbuffer())

        docker_file = minio_client.get_file(train_state_dict["bucket"], train_state_dict["dockerfile"])
        docker_file = BytesIO(docker_file)
        with open(train_state_dict["build_dir"] + train_state_dict["dockerfile"], 'wb') as f:
            f.write(docker_file.getbuffer())

        # build image
        image, logs = docker_client.images.build(path=train_state_dict["build_dir"], rm=True)
        container = docker_client.containers.create(image.id)

        # add endpoint to image
        endpoint = minio_client.get_file(train_state_dict["bucket"], train_state_dict["endpoint"])

        tarfile_name = f'{train_state_dict["endpoint"]}.tar'
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name=train_state_dict["endpoint"])
            data_file.size = len(endpoint)
            tar.addfile(data_file, io.BytesIO(endpoint))

        with open(tarfile_name, 'rb') as fd:
            respons = container.put_archive("/", fd)
            container.wait()

        container.commit(repository=train_state_dict["repo"], tag="latest")
        container.wait()
        return train_state_dict

    @task()
    def run_train(train_state_dict):
        docker_client = docker.from_env()
        container = docker_client.containers.run(train_state_dict["repo"], environment=train_state_dict["environment"], detach=True)

        exit_code = container.wait()["StatusCode"]
        print(f"{exit_code} run fin")
        f = open(f'results.tar', 'wb')
        results = container.get_archive('opt/pht_results')
        bits, stat = results
        for chunk in bits:
            f.write(chunk)
        f.close()

        return train_state_dict

    @task()
    def save_results(train_state_dict):
        minio_client = MinioClient(minio_server="minio:9000")
        with open(f'results.tar', 'rb') as results_tar:
            asyncio.run(
                minio_client.store_files(bucket=train_state_dict["bucket"], name="results.tar", file=results_tar))

    local_train = get_train_configuration()
    local_train = build_image(local_train)
    local_train = run_train(local_train)
    save_results(local_train)


run_aachen_train_dag = run_aachen_pht_train()
