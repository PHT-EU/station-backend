import requests
from station.app.db.session import SessionLocal
from sqlalchemy.orm import Session
from station.app.crud import dl_models, datasets, trains
from station.app.schemas.dl_models import DLModelCreate
from station.app.schemas.datasets import DataSetCreate


def create_data_sets(db: Session):
    ds_schema = DataSetCreate(
        name="cifar test set 1",

    )


def create_models(db: Session):
    pass


def seed_station_db():
    session = SessionLocal()
    create_models(session)
    create_data_sets(session)



if __name__ == '__main__':
    seed_station_db()
