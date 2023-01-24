import json
import sys
import os
import os.path

import docker
import docker.types
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

from docker.errors import APIError

from airflow.utils.dates import days_ago

from train_lib.docker_util.docker_ops import extract_train_config, extract_query_json
from train_lib.security.protocol import SecurityProtocol
from train_lib.clients import PHTFhirClient
from train_lib.docker_util.validate_master_image import validate_train_image
from train_lib.security.train_config import TrainConfig

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
def post_run_manual():
    @task()
    def get_train_image_info():
        context = get_current_context()
        repository, tag, env = [context['dag_run'].conf.get(_, None) for _ in
                                              ['repository', 'tag', 'env']]

        if not tag:
            tag = "latest"
        img = repository + ":" + tag



        train_id = repository.split("/")[-1]
        train_state_dict = {
            "train_id": train_id,
            "repository": repository,
            "tag": tag,
            "img": img,
            "env": env
        }

        return train_state_dict



    @task()
    def post_run_protocol(train_state):
        # Check if a post run protocol is specified
        config = TrainConfig(**train_state["config"])
        sp = SecurityProtocol(os.getenv("STATION_ID"), config=config)
        private_key_password = os.getenv("PRIVATE_KEY_PASSWORD", None)
        sp.post_run_protocol(img=train_state["img"],
                             private_key_path=os.getenv("PRIVATE_KEY_PATH"),
                             private_key_password=private_key_password
                             )

        return train_state

    @task()
    def rebase(train_state):
        base_image = ':'.join([train_state["repository"], 'base'])
        client = docker.from_env(timeout=120)
        to_container = client.containers.create(base_image)
        updated_tag = train_state["tag"]

        def _copy(from_cont, from_path, to_cont, to_path):
            """
            Copies a file from one container to another container
            :param from_cont:
            :param from_path:
            :param to_cont:
            :param to_path:
            :return:
            """
            tar_stream, _ = from_cont.get_archive(from_path)
            to_cont.put_archive(os.path.dirname(to_path), tar_stream)

        from_container = client.containers.create(train_state["img"])

        # Copy results to base image
        _copy(from_cont=from_container,
              from_path="/opt/pht_results",
              to_cont=to_container,
              to_path="/opt/pht_results")

        # Hardcoded copying of train_config.json
        _copy(from_cont=from_container,
              from_path="/opt/train_config.json",
              to_cont=to_container,
              to_path="/opt/train_config.json")

        print('Copied files into baseimage')

        print(f'Creating image: {train_state["repository"]}:{updated_tag}')
        print(type(to_container))
        # Rebase the train
        try:
            img = to_container.commit(repository=train_state["repository"], tag=train_state["tag"])
            # remove executed containers -> only images needed from this point
            print('Removing containers')
            to_container.remove()
            from_container.remove()
            return train_state
        except Exception as err:
            print(err)
            sys.exit()

    @task()
    def push_train_image(train_state):
        # skip if check results is true
        if train_state.get("check_results", True):
            return train_state

        client = docker.from_env()

        registry_address = os.getenv("HARBOR_URL").split("//")[-1]

        client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                     registry=registry_address)

        response = client.images.push(
            repository=train_state["repository"],
            tag=train_state["tag"],
            stream=False, decode=False
        )
        print(response)
        client.images.remove(f'{train_state["repository"]}:{train_state["tag"]}', noprune=False, force=True)
        client.images.remove(f'{train_state["repository"]}:base', noprune=False, force=True)

    train_state = get_train_image_info()
    train_state = post_run_protocol(train_state)
    train_state = rebase(train_state)
    push_train_image(train_state)


post_run_manual = post_run_manual()
