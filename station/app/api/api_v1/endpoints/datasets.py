from typing import Any, List

import pandas as pd
from sqlalchemy.orm import Session
from fastapi import APIRouter, Body, Depends, HTTPException
from station.app.api import dependencies

from station.app.schemas.datasets import DataSet, DataSetCreate, DataSetUpdate
from station.app.crud import datasets
from station.clients.minio import MinioClient

router = APIRouter()


@router.get("/datasets/{data_set_id}")
def get_data_set(data_set_id: Any, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, data_set_id)
    return db_dataset


@router.get("/datasts/{data_set_id}/download")
def download(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if db_dataset.storage_type == "csv":
        df = pd.read_csv(db_dataset.access_path)
        return df.to_json()
    else:
        return "can only return tabular data at the moment"


@router.post("/datasets")
def create_new_data_set(create_msg: DataSetCreate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.create(db, obj_in=create_msg)
    return db_dataset


@router.put("/datasets/{dataset_id}")
def update_data_set(dataset_id: Any, update_msg: DataSetUpdate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_data_set = datasets.get(db, id=dataset_id)
    new_db_data_set = datasets.update(db, db_data_set, update_msg)
    return new_db_data_set


@router.get("/datasets")
def read_all_data_sets(db: Session = Depends(dependencies.get_db)) -> List[DataSet]:
    all_datasets = datasets.get_multi(db=db, limit=None)
    print("tests")
    return all_datasets


@router.get("/datasets/minio/")
def get_data_sets_from_bucket():
    client = MinioClient()
    folders = client.list_data_sets()
    items = client.get_data_set_items("cifar10/batch_1/")
    print(len(list(items)))
    print(folders)
