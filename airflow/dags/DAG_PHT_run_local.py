import asyncio
import sys
from datetime import timedelta
import json
import os

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
        local_train_client = DockerClientLocalTrain(context)
        local_train_client.pull_master_image()
        local_train_client.build_train()
        local_train_client.run()
        local_train_client.save_results()
        #return local_train_client

    """@task()
    def pull_docker_image(local_train_client):
        local_train_client.pull_master_image()
        return local_train_client

    @task()
    def build_train(local_train_client):
        local_train_client.build_train()
        return local_train_client

    @task()
    def run_train(local_train_client):
        local_train_client.run()
        return local_train_client

    @task()
    def save_results(local_train_client):
        local_train_client.save_results()"""


    get_train_configuration()
    """local_train = pull_docker_image(local_train)
    local_train = build_train(local_train)
    local_train = run_train(local_train)
    save_results(local_train)"""


run_local = run_local()
