import requests
from station.app.db.session import SessionLocal
from sqlalchemy.orm import Session
from station.app.crud import dl_models, datasets, trains
from station.app.schemas.dl_models import DLModelCreate
from station.app.schemas.datasets import DataSetCreate
from conductor.examples.cifar_model import Cifar10Model
from conductor import serde


def create_data_sets(db: Session):
    ds_schema_minio = DataSetCreate(
        name="CIFAR test set 1",
        data_type="image",
        storage_type="minio",
        access_path="cifar/batch1"

    )

    ds_schema_file = DataSetCreate(
        name="CIFAR test set 2",
        data_type="image",
        storage_type="file"
    )

    db_ds_1 = datasets.create(db, obj_in=ds_schema_minio)
    db_ds_2 = datasets.create(db, obj_in=ds_schema_file)


def create_models(db: Session):
    cifar_model = Cifar10Model()

    model_dict = serde.serialize_lightning_model(cifar_model)

    model_create_schema = DLModelCreate(
        **model_dict,
        model_type="lightning"
    )

    db_model_1 = dl_models.create(db, obj_in=model_create_schema)
    db_model_2 = dl_models.create(db, obj_in=model_create_schema)


def seed_station_db():
    session = SessionLocal()
    create_models(session)
    create_data_sets(session)


if __name__ == '__main__':
    seed_station_db()
