from typing import Any, List
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from station.app.api import dependencies

from station.app.schemas.datasets import DataSet, DataSetCreate, DataSetUpdate
from station.app.crud import datasets
from station.clients.minio import MinioClient

router = APIRouter()


# TODO Response models
# TODO Error masanges
@router.post("", response_model=DataSet)
def create_new_data_set(create_msg: DataSetCreate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.create(db, obj_in=create_msg)
    return db_dataset


@router.put("/{dataset_id}", response_model=DataSet)
def update_data_set(dataset_id: Any, update_msg: DataSetUpdate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="DataSet not found.")
    new_db_dataset = datasets.update(db, db_dataset, update_msg)
    return new_db_dataset


@router.delete("/{dataset_id}", response_model=DataSet)
def delete_data_set(dataset_id: Any, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="DataSet not found.")
    db_data_set = datasets.remove(db, id=dataset_id)
    return db_data_set


@router.get("", response_model=List[DataSet])
def read_all_data_sets(db: Session = Depends(dependencies.get_db)) -> List[DataSet]:
    all_datasets = datasets.get_multi(db=db, limit=None)
    return all_datasets


@router.get("/{data_set_id}", response_model=DataSet)
def get_data_set(data_set_id: Any, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="DataSet not found.")
    return db_dataset


@router.get("/{data_set_id}/download")
def download(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="DataSet not found.")
    # TODO download as file
    if db_dataset.storage_type == "csv":
        df = pd.read_csv(db_dataset.access_path)
        return df.to_json()
    else:
        return "can only return tabular data at the moment"


@router.get("/minio/")
def get_data_sets_from_bucket():
    # TODO outsource minio functionality into separate endpoint file
    client = MinioClient()
    folders = client.list_data_sets()
    items = client.get_data_set_items("cifar10/batch_1/")
    if not items:
        raise HTTPException(status_code=404, detail="DataSet-Items not found.")
    print(len(list(items)))
    print(folders)
