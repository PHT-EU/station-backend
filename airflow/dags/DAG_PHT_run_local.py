
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import docker
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
from airflow.operators.python import get_current_context
from airflow.utils.dates import days_ago
from station.clients.station import StationAPIClient
from station.trains.local.build import build_train


def failure_callback(context):
    print(f"FAILURE CALLBACK -- Task {context['task'].task_id} failed")
    client = StationAPIClient.from_env()

    response = client.local_trains.post_failure_notification(context['dag_run'].conf['train_id'],
                                                             f"Train failed at task {context['task'].task_id}")
    print(response)


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
    'on_failure_callback': failure_callback,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}


@dag(
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['pht', 'local train'],
)
def run_local_train():
    @task(on_failure_callback=failure_callback)
    def get_local_train_config():
        context = get_current_context()
        train_id, env, volumes, master_image, custom_image = [context['dag_run'].conf.get(_, None) for _ in
                                                              ['train_id', 'env', 'volumes', 'master_image',
                                                               'custom_image']]

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
            "volumes": volumes,
            "master_image": master_image,
            "custom_image": custom_image
        }

        return train_config

    @task(on_failure_callback=failure_callback)
    def build_train_image(train_config):

        print("Building train image")
        print("config", train_config)

        connection = BaseHook.get_connection("pg_station")

        db_url = f"postgresql://{connection.login}:{connection.password}@{connection.host}:{connection.port}/" \
                 f"{connection.schema}"

        # create a session to the station database
        engine = create_engine(db_url)
        train_id = train_config['train_id']
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = session_local()

        client = StationAPIClient.from_env()

        train_files_archive = client.local_trains.download_train_archive(train_id)

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

    @task(on_failure_callback=failure_callback)
    def run_train(train_config):
        client = docker.from_env()
        environment = train_config.get("env", {})
        volumes = train_config.get("volumes", {})
        print("Volumes: ", volumes)
        container = client.containers.run(
            train_config['image'],
            environment=environment,
            volumes=volumes,
            detach=True,
            stderr=True,
            stdout=True,
        )

        output = container.wait()

        # print("Train Container ID: ", container.id)
        print("Train Container Logs: ", container.logs().decode("utf-8"))
        print("Train Container Exit Code: ", output['StatusCode'])

        return train_config

    @task(on_failure_callback=failure_callback)
    def update_train_status(train_config):
        client = StationAPIClient.from_env()
        context = get_current_context()
        print(dict(context))
        print(client.base_url)
        print(train_config)
        response = client.local_trains.update_train_status(train_config['train_id'], "completed")
        print(response)

    train_config = get_local_train_config()
    train_config = build_train_image(train_config)
    train_config = run_train(train_config)
    update_train_status(train_config)


local_train_dag = run_local_train()
