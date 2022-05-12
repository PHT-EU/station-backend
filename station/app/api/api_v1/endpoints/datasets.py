from typing import Any, List
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from station.app.api import dependencies

from station.app.schemas.datasets import DataSet, DataSetCreate, DataSetUpdate, DataSetStatistics
from station.app.datasets import statistics
from station.app.crud import datasets
from station.clients.minio import MinioClient

router = APIRouter()


# TODO Response models
# TODO Error messages
@router.post("", response_model=DataSet)
def create_new_data_set(create_msg: DataSetCreate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    dataset = datasets.get_by_name(db, name=create_msg.name)
    if dataset:
        raise HTTPException(status_code=400, detail=f"Dataset with name {create_msg.name} already exists.")
    try:
        db_dataset = datasets.create(db, obj_in=create_msg)
        if not db_dataset:
            raise HTTPException(status_code=404, detail="Error while creating new dataset.")
        return db_dataset
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found.")


@router.put("/{dataset_id}", response_model=DataSet)
def update_data_set(dataset_id: Any, update_msg: DataSetUpdate, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    new_db_dataset = datasets.update(db=db, db_obj=db_dataset, obj_in=update_msg)
    return new_db_dataset


@router.delete("/{dataset_id}", response_model=DataSet)
def delete_data_set(dataset_id: Any, db: Session = Depends(dependencies.get_db)) -> DataSet:
    db_dataset = datasets.get(db, dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
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
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return db_dataset


@router.get("/{data_set_id}/download")
def download(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    # TODO download as file


@router.get("/minio/")
def get_data_sets_from_bucket():
    # TODO outsource minio functionality into separate endpoint file
    client = MinioClient()
    folders = client.list_data_sets()
    items = client.get_data_set_items("cifar10/batch_1/")
    if not items:
        raise HTTPException(status_code=404, detail="Dataset-Items not found.")
    print(len(list(items)))
    print(folders)


@router.get("/{data_set_id}/stats", response_model=DataSetStatistics)
def get_data_set_statistics(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    dataframe = datasets.get_data(db, data_set_id)
    if dataframe is None or dataframe.empty:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    try:
        stats = statistics.get_dataset_statistics(dataframe)
        return stats
    except TypeError:
        raise HTTPException(status_code=400, detail="Dataset has to be given as a dataframe.")


@router.get("/{data_set_id}/stats/{target_field}")
def get_class_distribution(data_set_id: Any, target_field: str, db: Session = Depends(dependencies.get_db)):
    dataframe = datasets.get_data(db, data_set_id)
    if dataframe.empty:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if target_field in dataframe.columns:
        try:
            distribution = statistics.get_class_distribution(dataframe, target_field)
            return distribution
        except TypeError:
            raise HTTPException(status_code=400, detail="Dataset has to be given as a dataframe.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Class counts are not computed for numerical data columns.")
    else:
        raise HTTPException(status_code=404, detail="Targetfield not found in dataset.")
