from io import BytesIO
from typing import Any, List

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from loguru import logger

from station.app.schemas.users import User
from station.app.api import dependencies

from station.app.schemas.datasets import DataSet, DataSetCreate, DataSetUpdate, DataSetStatistics, MinioFile
from station.app.datasets import statistics
from station.app.crud import datasets
from station.clients.minio import MinioClient
from station.ctl.constants import DataDirectories

router = APIRouter()


@router.post("", response_model=DataSet)
def create_new_data_set(
        create_msg: DataSetCreate,
        db: Session = Depends(dependencies.get_db),
        user: User = Depends(dependencies.authorized_user)
) -> DataSet:

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
    except NotImplementedError:
        raise HTTPException(status_code=422, detail=f"Storage type {create_msg.storage_type} not possible yet.")


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


@router.post("/{dataset_id}/files")
async def upload_data_set_file(dataset_id: str,
                               files: List[UploadFile] = File(description="Multiple files as UploadFile"),
                               db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided.")

    minio_client = MinioClient()
    await minio_client.save_dataset_files(db_dataset.id, files)


@router.get("/{data_set_id}/files", response_model=List[MinioFile])
async def get_data_set_files(data_set_id: str, file_name: str = None, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {data_set_id} not found.")

    minio_client = MinioClient()
    items = minio_client.get_minio_dir_items(DataDirectories.DATASETS, data_set_id)
    if file_name:
        pass
    return items


@router.delete("/{data_set_id}/files")
async def delete_file_from_dataset(data_set_id: str, file_name: str, db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {data_set_id} not found.")

    minio_client = MinioClient()
    minio_client.delete_file(DataDirectories.DATASETS.value, file_name)


@router.get("/{data_set_id}/download", response_class=StreamingResponse)
async def download(data_set_id: Any, archive_type: str = "tar", db: Session = Depends(dependencies.get_db)):
    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    minio_client = MinioClient()
    items = minio_client.get_minio_dir_items(DataDirectories.DATASETS, data_set_id)

    if len(items) == 0:
        raise HTTPException(status_code=404, detail="No files found.")
    elif len(items) == 1:
        data = minio_client.get_file(str(DataDirectories.DATASETS.value), items[0].full_path)
        obj = BytesIO(data)
        return StreamingResponse(content=obj, media_type="application/octet-stream")

    else:
        archive = minio_client.make_dataset_archive(data_set_id, items=items, archive_type=archive_type)
        return StreamingResponse(content=archive, media_type="application/zip")


@router.get("/{data_set_id}/stats", response_model=DataSetStatistics)
def get_data_set_statistics(data_set_id: Any, file_name: str = None, db: Session = Depends(dependencies.get_db)):

    db_dataset = datasets.get(db, data_set_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    minio_client = MinioClient()
    items = minio_client.get_minio_dir_items(DataDirectories.DATASETS, data_set_id)
    if len(items) == 0 and not db_dataset.fhir_server:
        raise HTTPException(status_code=404, detail="No files found in the dataset.")

    if db_dataset.data_type in {"hybrid", "structured"}:
        if file_name:
            items = [item for item in items if item.file_name == file_name]
            if len(items) == 0:
                raise HTTPException(status_code=404, detail=f"File {file_name} not found.")
        file_content = minio_client.get_file(DataDirectories.DATASETS, items[0].full_path)

        try:
            df = statistics.load_tabular(items[0], file_content)
            stats = statistics.get_dataset_statistics(df)
            dataset = datasets.add_stats(db, data_set_id, stats)
            return stats

        except TypeError as e:
            raise HTTPException(status_code=400, detail=f"File {file_name} is not in a supported tabular format.")

    else:
        raise HTTPException(status_code=400, detail=f"Data type {db_dataset.data_type} is not supported yet.")
