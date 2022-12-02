import io
import tarfile
from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from station.app.api import dependencies
from station.app.config import clients

from station.app.schemas import local_trains

from station.app.crud.crud_local_train import local_train
from station.app.crud.local_train_master_image import local_train_master_image
from station.app.schemas.datasets import MinioFile
from station.clients.minio import MinioClient
from station.ctl.constants import DataDirectories
from station.trains.local.airflow import run_local_train

router = APIRouter()


@router.post("", response_model=local_trains.LocalTrain)
def create_local_train(create_msg: local_trains.LocalTrainCreate, db: Session = Depends(dependencies.get_db)):
    """
    creae a database entry for a new train with preset names from the create_msg

    @param create_msg: information about the new train
    @param db: reference to the postgres database
    @return:
    """
    train = local_train.create(db, obj_in=create_msg)
    return train


@router.get("/{train_id}", response_model=local_trains.LocalTrain)
def get_local_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    train = local_train.get(db, train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train ({train_id}) not found")
    return train


@router.get("", response_model=List[local_trains.LocalTrain])
def get_local_trains(db: Session = Depends(dependencies.get_db), skip: int = 0, limit: int = 100):
    trains = local_train.get_multi(db, skip=skip, limit=limit)

    return trains


@router.put("/{train_id}", response_model=local_trains.LocalTrain)
def update_local_train(train_id: str, update_msg: local_trains.LocalTrainUpdate,
                       db: Session = Depends(dependencies.get_db)):
    train = local_train.get(db, train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train ({train_id}) not found")

    train = local_train.update(db, db_obj=train, obj_in=update_msg)
    return train


@router.delete("/{train_id}", response_model=local_trains.LocalTrain)
def delete_local_train(train_id: str, db: Session = Depends(dependencies.get_db)):
    train = local_train.get(db, train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train ({train_id}) not found")

    train = local_train.remove(db, id=train_id)
    return train


@router.post("/{train_id}/run", response_model=local_trains.LocalTrainExecution)
async def trigger_train_execution(train_id: str, run_config: local_trains.LocalTrainRunConfig,
                          db: Session = Depends(dependencies.get_db)):
    train = local_train.get(db, train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train ({train_id}) not found")

    execution = run_local_train(
        db=db,
        train_id=train_id,
        config_id=run_config.config_id,
        dataset_id=run_config.dataset_id,
    )

    return execution


@router.post("/{train_id}/files")
async def upload_train_files(train_id: str,
                             files: List[UploadFile] = File(description="Multiple files as UploadFile"),
                             db: Session = Depends(dependencies.get_db)) -> List[MinioFile]:
    db_train = local_train.get(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Local train ({train_id}) not found.")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided.")

    state = db_train.state

    if state.configuration_state != local_trains.LocalTrainConfigurationStep.image_configured.value:
        raise HTTPException(status_code=400, detail="Train image is not configured. Select an image first before up"
                                                    "loading files.")

    resp = await clients.minio.save_local_train_files(db_train.id, files)

    state.configuration_status = local_trains.LocalTrainConfigurationStep.files_uploaded.value
    db.commit()
    return resp


@router.get("/{train_id}/files", response_model=List[MinioFile])
async def get_train_files(train_id: str, file_name: str = None, db: Session = Depends(dependencies.get_db)):
    db_train = local_train.get(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Local train ({train_id}) not found.")

    items = clients.minio.get_minio_dir_items(DataDirectories.LOCAL_TRAINS.value, str(db_train.id))
    if file_name:
        pass
    return items


@router.get("/{train_id}/archive", response_class=StreamingResponse)
async def get_train_archive(train_id: str, db: Session = Depends(dependencies.get_db)):
    db_train = local_train.get(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Local train ({train_id}) not found.")
    resp = clients.minio.get_local_train_archive(str(db_train.id))
    return StreamingResponse(content=resp, media_type="application/octet-stream")
