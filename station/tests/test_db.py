from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from station.app.db.base import Base

import uuid, random
from station.app.crud.crud_notifications import *
from station.app.crud.crud_train_configs import *
from station.app.models.notification import Notification
from station.app.db.session import SessionLocal
from fastapi.encoders import jsonable_encoder
from station.app.crud.crud_docker_trains import *
from station.app.crud.crud_datasets import *
from station.app.schemas.dl_models import *
from station.app.models.dl_models import *

# Create new sqlite database for testing

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def test_crud_docker_train():

    session = TestingSessionLocal()

    list_ids = []

    train_id = str(uuid.uuid4())

    crud_docker_train = CRUDDockerTrain(DockerTrain)

    docker_train_create_obj = DockerTrainCreate(train_id=train_id)

    crud_create_db_train = crud_docker_train.create(session, obj_in=docker_train_create_obj)
    print("CRUD CreateDockerTrain : {}".format(jsonable_encoder(crud_create_db_train)))

    crud_get_db_train = crud_docker_train.get_by_train_id(session, train_id)
    print("CRUD DockerTrain : {}".format(jsonable_encoder(crud_get_db_train)))

    docker_train_all = crud_docker_train.get_multi(session)


    for docker_train in docker_train_all:
        print("Docker Train with ID {} exists in the database.".format(docker_train.id))
        list_ids.append(docker_train.id)

    for n in list_ids:
        crud_docker_train.remove(session, id=n)
        print("Docker Train with ID {} got deleted.".format(n))

    session.close()


def test_crud_notifications():

    session = TestingSessionLocal()

    list_ids = []

    crud_notifications = CRUDNotifications(Notification)

    notification_create_obj = NotificationCreate(target_user='all', topic="DAG execution", message="DAG has been executed successfully")
    print("NotificationCreate : {}".format(jsonable_encoder(notification_create_obj)))

    crud_create_db_notification = crud_notifications.create(session, obj_in=notification_create_obj)
    print("CRUD create db_notification : {}".format(jsonable_encoder(crud_create_db_notification)))



    notifications_all = crud_notifications.get_multi(session)


    for notification in notifications_all:
        print("Notification with ID {} exists in the database.".format(notification.id))
        list_ids.append(notification.id)

    for n in list_ids:
        crud_notifications.remove(session, id=n)
        print("Notfication with ID {} got deleted.".format(n))


    session.close()


def test_crud_train_config():

    session = TestingSessionLocal()

    list_ids = []

    crud_train_config = CRUDDockerTrainConfig(DockerTrainConfig)

    id = random.randint(0, 10000)
    name = "DockerTrainConfig Example/" + str(id)

    train_config_create = DockerTrainConfigCreate(name=name)
    print("DockerTrainConfigCreate : {}".format(jsonable_encoder(train_config_create)))

    crud_train_config_create = crud_train_config.create(session, obj_in=train_config_create)
    print("CRUDDockerTrainConfigCreate : {}".format(jsonable_encoder(crud_train_config_create)))

    id = crud_train_config_create.id

    crud_train_config_get = crud_train_config.get(session, id=id)
    print("CRUDDockerTrainConfigGet : {}".format(jsonable_encoder(crud_train_config_get)))

    train_config_all = crud_train_config.get_multi(session)


    for train_config in train_config_all:
        print("Train Conig with ID {} exists in the database.".format(train_config.id))
        list_ids.append(train_config.id)

    for n in list_ids:
        crud_train_config.remove(session, id=n)
        print("Train Config with ID {} got deleted.".format(n))

    session.close()


def test_crud_datasets():

    session = TestingSessionLocal()

    list_ids = []

    crud_datasets = CRUDBase(DataSet)

    id = random.randint(0, 10000)
    name = "Dataset Example/" + str(id)

    datasets_create = DataSetCreate(name=name, data_type='image', storage_type='minio')
    print("DatasetsCreate : {}".format(jsonable_encoder(datasets_create)))

    crud_datasets_create = crud_datasets.create(session, obj_in=datasets_create)
    print("CRUDDatasetsCreate : {}".format(jsonable_encoder(crud_datasets_create)))

    id = crud_datasets_create.id

    crud_datasets_get = crud_datasets.get(session, id=id)
    print("CRUDDatasetsGet : {}".format(jsonable_encoder(crud_datasets_get)))

    datasets_all = crud_datasets.get_multi(session)


    for dataset in datasets_all:
        print("Dataset with ID {} exists in the database.".format(dataset.id))
        list_ids.append(dataset.id)

    for n in list_ids:
        crud_datasets.remove(session, id=n)
        print("Dataset with ID {} got deleted.".format(n))

    session.close()

def test_crud_torch_model():

    session = TestingSessionLocal()

    list_ids = []

    model_id = str(uuid.uuid4())

    crud_torch_models = CRUDBase(TorchModel)

    torch_model_create = TorchModelCreate(model_id=model_id)
    print("TorchModelCreate : {}".format(jsonable_encoder(torch_model_create)))

    crud_torch_model_create = crud_torch_models.create(session, obj_in=torch_model_create)
    print("CRUDTorchModelCreate : {}".format(jsonable_encoder(crud_torch_model_create)))

    torch_id = crud_torch_model_create.id

    crud_torch_model_get = crud_torch_models.get(session, id=torch_id)
    print("CRUDTorchModelGet : {}".format(jsonable_encoder(crud_torch_model_get)))

    torch_model_all = crud_torch_models.get_multi(session)


    for torch_model in torch_model_all:
        print("Torch Model with ID {} exists in the database.".format(torch_model.id))
        list_ids.append(torch_model.id)

    for n in list_ids:
        crud_torch_models.remove(session, id=n)
        print("Torch Model with ID {} got deleted.".format(n))

    session.close()
