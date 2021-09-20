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


@dag(default_args=default_args, schedule_interval=None, start_date=days_ago(2), tags=['pht', 'train'])
def run_aachen_pht_train():
    @task()
    def get_train_image_info():
        context = get_current_context()
        repository, tag, env, volumes = [context['dag_run'].conf.get(_, None) for _ in
                                         ['repository', 'tag', 'env', 'volumes']]
        img = repository + ":" + tag

        train_state_dict = {
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env,
            "volumes": volumes
        }
        print(train_state_dict)
        return train_state_dict

    @task()
    def pull_docker_image(train_state):
        client = docker.from_env()
        registry_address = os.getenv("HARBOR_AACHEN_API_URL").split("//")[-1]
        print(registry_address)
        client.login(username=os.getenv("HARBOR_AACHEN_API_URL"), password=os.getenv("HARBOR_PW"),
                     registry=registry_address)

        client.images.pull(repository=train_state["repository"], tag=train_state["tag"])

        # Pull base image as well
        client.images.pull(repository=train_state["repository"], tag='base')
        # Make sure the image with the desired tag is there.
        images = client.images.list()
        image_tags = sum([i.tags for i in images], [])
        assert (':'.join([train_state["repository"], train_state["tag"]]) in image_tags)
        print("Image was successfully pulled.")
        assert (':'.join([train_state["repository"], 'base']) in image_tags)
        print("Base image was successfully pulled.")

    @task()
    def execute_container(train_state):
        client = docker.from_env()
        environment = train_state.get("env", {})
        volumes = train_state.get("volumes", {})

    get_train_image_info()


run_aachen_train_dag = run_aachen_pht_train()
