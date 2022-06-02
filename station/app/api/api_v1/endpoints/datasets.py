from typing import Any, List
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from station.app.api import dependencies

from station.app.schemas.datasets import DataSet, DataSetCreate, DataSetUpdate, DataSetStatistics
from station.app.datasets import statistics
from station.app.crud import datasets
from station.clients.minio import MinioClient

router = APIRouter()


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
        raise HTTPException(status_code=404, detail=f"Dataset file not found at {create_msg.access_path}.")


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


@router.post("/{data_set_id}/files")
async def upload_data_set_file(data_set_id: str, file: UploadFile = File(...),
                               db: Session = Depends(dependencies.get_db)):
    pass


@router.get("/{data_set_id}/files")
def get_data_set_files(data_set_id: str, file_name: str, db: Session = Depends(dependencies.get_db)):
    pass


@router.get("/{data_set_id}/download")
def download(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    # TODO download as file


@router.get("/{data_set_id}/stats", response_model=DataSetStatistics)
def get_data_set_statistics(data_set_id: Any, db: Session = Depends(dependencies.get_db)):
    try:
        dataframe = datasets.get_data(db, data_set_id)
    except NotImplementedError:
        raise HTTPException(status_code=422, detail="Method just specified for CSV-Data.")
    if dataframe is None or dataframe.empty:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    try:
        stats = statistics.get_dataset_statistics(dataframe)
        try:
            dataset = datasets.add_stats(db, data_set_id, stats)
        except:
            raise HTTPException(status_code=500, detail="Upload to database did not work.")
        return stats
    except TypeError:
        raise HTTPException(status_code=400, detail="Dataset has to be given as a dataframe.")


