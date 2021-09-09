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
from train_lib.docker_util.validate_master_image import validate_train_image

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
def run_local():
    @task()
    def test_note():
        print("DAG run")

    test_note()


run_local = run_local()
