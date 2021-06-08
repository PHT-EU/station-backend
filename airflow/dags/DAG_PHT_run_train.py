import sys
import datetime
import docker

import requests
import json
import os

from docker.errors import APIError
from train_lib.docker_util.docker_ops import extract_train_config
from train_lib.security.SecurityProtocol import SecurityProtocol

from airflow.operators.python import PythonOperator
import airflow

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'schedule_interval': None,  # So the DAG is not scheduled automatically
    'start_date': datetime.datetime(2019, 12, 30),
    'email': ['station_airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
}

dag = airflow.DAG(dag_id='run_train', default_args=default_args, schedule_interval=None)


def pull_docker_image(**context):
    repository, tag = [context['dag_run'].conf[_] for _ in ['repository', 'tag']]

    client = docker.from_env()
    # Harbor login

    login_result = client.login(username=os.getenv("HARBOR_USER"),
                                password=os.getenv("HARBOR_PW"),
                                registry="harbor.personalhealthtrain.de")
    print(login_result)

    harbor_repo = f"harbor.personalhealthtrain.de/{int(os.getenv('STATION_ID'))}/{repository}"
    # Pull the image.
    client.images.pull(repository=harbor_repo, tag=tag)
    # Pull base image as well
    client.images.pull(repository=harbor_repo, tag='base')
    # Make sure the image with the desired tag is there.
    images = client.images.list()
    image_tags = sum([i.tags for i in images], [])
    assert (':'.join([repository, tag]) in image_tags)
    print("Image was successfully pulled.")
    assert (':'.join([repository, 'base']) in image_tags)
    print("Baseimage was successfully pulled.")


def pre_run_protocol(**context):
    repository, tag = [context['dag_run'].conf[_] for _ in ['repository', 'tag']]
    img = repository + ":" + tag
    config = extract_train_config(img)
    sp = SecurityProtocol(os.getenv("STATION_ID"), config=config)
    sp.pre_run_protocol(img=img, private_key_path=os.getenv("STATION_PRIVATE_KEY_PATH"))


def execute_container(**context):
    conf = ['repository', 'tag', 'cmd', 'entrypoint']
    repository, tag, cmd, entrypoint = [context['dag_run'].conf.get(_, None) for _ in conf]
    image = ':'.join([repository, tag])
    # create name fro the container to be able to grab the container in later tasks
    container_name = f'{repository.split("/")[-1]}.{tag}'
    client = docker.from_env()
    print(f"Running command {cmd}")
    environment = context['dag_run'].conf['.env'] if '.env' in context['dag_run'].conf.keys() else {}
    print(f"Environment input for container: {environment}")

    if cmd and entrypoint:
        # Run container with a specified command and entrypoint
        print("Running with custom entrypoint")
        try:
            container = client.containers.run(image=image, command=cmd, detach=True, entrypoint=entrypoint,
                                              environment=environment, name=container_name)

        # If the container is already in use remove it
        except APIError as e:
            print(e)
            client.containers.remove(container_name)
            container = client.containers.run(image=image, command=cmd, detach=True, entrypoint=entrypoint,
                                              environment=environment, name=container_name)

    else:
        # Run container with default command and entrypoint
        print("Running with default command")
        try:
            container = client.containers.run(image, environment=environment,
                                              name=container_name, detach=True)
        # If the container is already in use remove it
        except APIError as e:
            print(e)
            client.containers.remove(container_name)
            container = client.containers.run(image, environment=environment,
                                              name=container_name, detach=True)

    exit_code = container.wait()["StatusCode"]
    container.commit(repository=repository, tag=tag)
    print(container.logs().decode("utf-8"))
    if exit_code != 0:
        print(f"The command {cmd} resulted in a non-zero exit code: {exit_code}")
        sys.exit()


def post_run_protocol(**context):
    repository, tag = [context['dag_run'].conf[_] for _ in ['repository', 'tag']]
    img = repository + ":" + tag
    config = extract_train_config(img)
    sp = SecurityProtocol(os.getenv("STATION_ID"), config=config)
    sp.post_run_protocol(img=img, private_key_path=os.getenv("STATION_PRIVATE_KEY_PATH"))


def rebase(**context):
    repository, tag = [context['dag_run'].conf[_] for _ in ['repository', 'tag']]
    # Build container name from context to get executed container
    # container_name = f'{repository.split("/")[-1]}.{tag}'
    base_image = ':'.join([repository, 'base'])
    client = docker.from_env(timeout=120)
    # Grab the base image to rebase the train, only adds one layer in total and not one per station
    to_container = client.containers.create(base_image)
    updated_tag = tag

    # TODO only copy the results directory + train_config.json

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

    from_container = client.containers.create(f"{repository}:latest")
    # Extract added and updated files
    # try:
    #     from_container = client.containers.create(f"{repository}:latest")
    #     files = from_container.diff()
    # except Exception as err:
    #     print(err)
    #     sys.exit()

    # print('Copying new files into baseimage')
    # for file in files:
    #     print(file)
    #     _copy(from_cont=from_container,
    #           from_path=file['Path'],
    #           to_cont=to_container,
    #           to_path=file['Path'])

    # Copy results to base image
    _copy(from_cont=from_container,
          from_path="/opt/pht_results",
          to_cont=to_container,
          to_path="/opt/pht_results")

    # Hardcoded copying of train_config.json
    # TODO improve this
    _copy(from_cont=from_container,
          from_path="/opt/train_config.json",
          to_cont=to_container,
          to_path="/opt/train_config.json")

    print('Copied files into baseimage')

    print(f'Creating image: {repository}:{updated_tag}')
    # print(type(to_container))
    # Rebase the train
    try:
        img = to_container.commit(repository=repository, tag="base")
        # remove executed containers -> only images needed from this point
        print('Removing containers')
        to_container.remove()
        from_container.remove()
    except Exception as err:
        print(err)
        sys.exit()


def push_docker_image(**context):
    conf = ['repository', 'tag']
    repository, tag = [context['dag_run'].conf[_] for _ in conf]
    # Run container again
    client = docker.from_env()
    # Login needed?
    client.login(username=os.getenv("HARBOR_USER"), password=os.getenv("HARBOR_PW"),
                 registry='harbor.personalhealthtrain.de')
    # TODO error handling
    response = client.images.push(repository=repository, tag=tag, stream=False, decode=False)
    print(response)


def put_harbor_label(**context):
    # https://redmine.medic.uni-tuebingen.de/issues/1733
    # Assumption that project name and project_repository can be extracted from the repository path from the last two
    # labels

    # TODO change to use environment variables
    repository, tag = [context['dag_run'].conf[_] for _ in ['repository', 'tag']]
    project, project_repo = repository.split('/')[-2:]
    # config = configparser.ConfigParser()
    # conf_file = context['dag_run'].conf['conf']
    # print(f"Reading config file '{conf_file}':\n[credentials]\n"
    #       "USERNAME = <USERNAME>\nPASSWORD = <PASSWORD>\n"
    #       "API_URL = <HARBOR_API_URL>")
    # config.read(conf_file)
    # conf = ['API_URL', 'USERNAME', 'PASSWORD']
    # try:
    #     api, username, password = [config["credentials"][_] for _ in conf]
    # except Exception as err:
    #     print("Credentials could not be parsed.")
    #     sys.exit()
    api = os.getenv("HARBOR_API_URL")
    username = os.getenv("HARBOR_USER")
    password = os.getenv("HARBOR_PW")
    url = f'{api}/projects/{project}/repositories/{project_repo}/artifacts/{tag}/labels'
    print(f'Url for changing the label: {url}')

    # Label being added currently hardcoded
    # label_added = {'id': 7}  # pht_next id Wissenschaftsnetz
    label_added = {'id': 2}  # pht_next id de.NBI cloud
    print(f'Label to be added: {label_added}')
    headers_add = {'accept': 'application/json', 'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers_add, data=json.dumps(label_added),
                                 auth=(username, password))
        response.raise_for_status()
        print(f'Label with id "{label_added}" has been added.')
        return
    except requests.exceptions.HTTPError as e:
        e_msg = e.response.json()
        print(e_msg)
        if e_msg['errors'][0]['code'] == 'CONFLICT' and 'is already added to the artifact' in e_msg['errors'][0][
            'message']:
            print('Label has already been placed on the artifact')
            return
        else:
            sys.exit()
    except Exception as err:
        print(err)
        sys.exit()


t1 = PythonOperator(
    task_id='pull_docker_image',
    provide_context=True,
    python_callable=pull_docker_image,
    dag=dag,
)

t2 = PythonOperator(
    task_id="pre-run_protocol",
    provide_context=True,
    python_callable=pre_run_protocol,
    execution_timeout=datetime.timedelta(minutes=5),
    dag=dag
)

t3 = PythonOperator(
    task_id='execute_container',
    provide_context=True,
    python_callable=execute_container,
    execution_timeout=datetime.timedelta(minutes=1),
    dag=dag,
)

t4 = PythonOperator(
    task_id="post-run_protocol",
    provide_context=True,
    python_callable=post_run_protocol,
    execution_timeout=datetime.timedelta(minutes=5),
    dag=dag
)

# t5 = PythonOperator(
#     task_id='rebase',
#     provide_context=True,
#     python_callable=rebase,
#     execution_timeout=datetime.timedelta(minutes=5),
#     dag=dag,
# )

t6 = PythonOperator(
    task_id='push_docker_image',
    provide_context=True,
    python_callable=push_docker_image,
    execution_timeout=datetime.timedelta(minutes=1),
    dag=dag,
)

t7 = PythonOperator(
    task_id='put_harbor_label',
    provide_context=True,
    python_callable=put_harbor_label,
    execution_timeout=datetime.timedelta(minutes=1),
    dag=dag,
)

t1 >> t2 >> t3 >> t4 >> t6 >> t7
