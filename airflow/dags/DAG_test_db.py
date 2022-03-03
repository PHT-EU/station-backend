import asyncio
import datetime
import logging
import random
import tarfile
import os
import time, datetime
from io import BytesIO
import shutil
import docker
import uuid
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.utils.dates import days_ago


from station.app.crud.crud_docker_trains import *
from station.app.models import docker_trains
from station.app.schemas.docker_trains import *
from station.clients.airflow.utils import UtilityFunctions
from station.app.crud.crud_notifications import *
from station.app.models import notification
from station.app.schemas.notifications import *
from pydantic import BaseModel
from station.app.crud.crud_docker_trains import *

from train_lib.clients import PHTFhirClient
from station.clients.minio import MinioClient




default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
}


@dag(default_args=default_args, schedule_interval=None, start_date=days_ago(2), tags=['pht', 'train'])
def run_local_test_db():
    """
    Defins a DAG simular to the run train only for local execution of test Trains dosent contain any of the sequrety
    and stores the restults not ecripted into the minIO.
    @return:
    """



    @task()
    def create_example_train() -> dict:
        """
        extra the train state dict form airflow context

        @return: train_state_dict
        """
        utils = UtilityFunctions()

        session = utils.create_session()
        session = session()


        train_id = str(uuid.uuid4())

        crud_docker_train = CRUDDockerTrain(DockerTrain)

        docker_train_create_obj = DockerTrainCreate(train_id=train_id)

        crud_create_db_train = crud_docker_train.create(session, obj_in=docker_train_create_obj)
        print("CRUD DockerTrain.create.train_id : {}".format(crud_create_db_train.train_id))

        crud_get_db_train = crud_docker_train.get_by_train_id(session, train_id)
        print("CRUD DockerTrain.get_by_train_id : {}".format(crud_get_db_train.train_id))

        session.close()


        return {"success" : True}

    @task()
    def create_notification_of_dag_status() -> dict:
        """
        extra the train state dict form airflow context

        @return: train_state_dict
        """
        utils = UtilityFunctions()

        session = utils.create_session()
        session = session()

        notification_id = random.randint(1, 100)

        crud_notifications = CRUDNotifications(Notification)

        notifcation_create_obj = NotificationCreate(id=notification_id, topic="DAG execution", message="DAG has been executed successfully")
        print("NotificationCreate : {}".format(notifcation_create_obj.message))

        crud_create_db_notification = crud_notifications.create_notification(session, obj_in=notifcation_create_obj)

        crud_get_db_notification = crud_notifications.get_notification_by_id(session, notification_id)
        print("Notification with ID : {} contians message : {}".format(crud_get_db_notification.id, crud_get_db_notification.message))

        session.close()



        return {"success" : True}


    local_train = create_example_train()
    local_train = create_notification_of_dag_status()

run_local = run_local_test_db()
