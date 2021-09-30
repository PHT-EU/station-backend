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
from train_lib.fhir import PHTFhirClient
from train_lib.security import SecurityProtocol
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

from station.clients.docker.local_run_client import DockerClientLocalTrain

from train_lib.docker_util.docker_ops import extract_train_config, extract_query_json
from train_lib.security.SecurityProtocol import SecurityProtocol
from train_lib.fhir import PHTFhirClient

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
    @task()
    def get_train_configuration():
        context = get_current_context()
        repository, tag, env, volumes, build_dir = [context['dag_run'].conf.get(_, None) for _ in
                                                    ['repository', 'tag', 'env', 'volumes', 'build_dir']]
        img = repository + ":" + tag
        train_state_dict = {
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes,
            "build_dir": build_dir,
            "bucket_name": "localtrain"
        }
        return train_state_dict

    @task()
    def pull_docker_image(train_state_dict):
        docker_client = docker.from_env()
        harbor_address = os.getenv("HARBOR_API_URL")
        docker_client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                            registry=harbor_address)
        docker_client.images.pull(repository=train_state_dict["repository"], tag=train_state_dict["tag"])

        images = docker_client.images.list()
        print(images)
        return train_state_dict

    @task()
    def build_train(train_state_dict):
        docker_client = docker.from_env()
        minio_client = MinioClient(minio_server="minio:9000")
        docker_file = f'''
                            FROM {train_state_dict["img"]}
                            RUN mkdir /opt/pht_results
                            RUN mkdir /opt/pht_train
                            RUN chmod -R +x /opt/pht_train
                            CMD ["python", "/opt/pht_train/endpoint.py"]
                            '''
        docker_file = BytesIO(docker_file.encode("utf-8"))

        image, logs = docker_client.images.build(fileobj=docker_file)
        container = docker_client.containers.create(image.id)
        print(image.id)

        endpoint = minio_client.get_file(train_state_dict["bucket_name"], "endpoint.py")
        name = "endpoint.py"

        tarfile_name = f"{name}.tar"
        with tarfile.TarFile(tarfile_name, 'w') as tar:
            data_file = tarfile.TarInfo(name='endpoint.py')
            data_file.size = len(endpoint)
            tar.addfile(data_file, io.BytesIO(endpoint))

        with open(tarfile_name, 'rb') as fd:
            respons = container.put_archive("/opt/pht_train", fd)
            container.wait()
        print(respons)
        container.commit(repository="local_train", tag="latest")
        container.wait()

        return train_state_dict

    @task()
    def run_train(train_state_dict):
        docker_client = docker.from_env()
        container = docker_client.containers.run("local_train", detach=True)
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
                minio_client.store_files(bucket=train_state_dict["bucket_name"], name="results.tar", file=results_tar))

    local_train = get_train_configuration()
    local_train = pull_docker_image(local_train)
    local_train = build_train(local_train)
    local_train = run_train(local_train)
    save_results(local_train)


run_local = run_local()
