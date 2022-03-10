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
#from station.app.models.dl_models import *

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

