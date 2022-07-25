import io
import tarfile
from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException

from station.app.api import dependencies

from station.app.schemas import local_trains

from station.app.crud.crud_local_train import local_train
from station.app.crud.local_train_master_image import local_train_master_image
from station.clients.minio import MinioClient

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


@router.post("/{train_id}/files")
async def upload_train_files(train_id: str,
                             files: List[UploadFile] = File(description="Multiple files as UploadFile"),
                             db: Session = Depends(dependencies.get_db)) -> List[dict]:
    db_train = local_train.get(db, train_id)
    if not db_train:
        raise HTTPException(status_code=404, detail=f"Local train ({train_id}) not found.")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided.")
    minio_client = MinioClient()
    resp = await minio_client.save_local_train_files(db_train.id, files)
    return resp


@router.post("/master-images", response_model=local_trains.LocalTrainMasterImage)
def add_master_image(
        add_master_image_msg: local_trains.LocalTrainMasterImageCreate,
        db: Session = Depends(dependencies.get_db)
):
    # check if id already exists
    if local_train_master_image.get_by_image_id(db, add_master_image_msg.image_id):
        raise HTTPException(status_code=400,
                            detail=f"Image with the given id: ({add_master_image_msg.image_id}) already exists")
    image = local_train_master_image.create(db, obj_in=add_master_image_msg)
    return image


@router.get("/master-images/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def get_master_image(image_id: str, db: Session = Depends(dependencies.get_db)):
    image = local_train_master_image.get(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.get("/master-images", response_model=List[local_trains.LocalTrainMasterImage])
def list_master_images(db: Session = Depends(dependencies.get_db), skip: int = 0, limit: int = 100, sync: bool = False):
    if sync:
        local_train_master_image.sync_with_harbor(db)
    images = local_train_master_image.get_multi(db, skip=skip, limit=limit)
    return images


@router.put("/master-images/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def update_master_image(image_id: str, update_msg: local_trains.LocalTrainMasterImageUpdate,
                        db: Session = Depends(dependencies.get_db)):
    db_image = local_train_master_image.get(db, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = local_train_master_image.update(db, db_obj=db_image, obj_in=update_msg)
    return image


@router.delete("/master-images/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def delete_master_image(image_id: str, db: Session = Depends(dependencies.get_db)):
    db_image = local_train_master_image.get(db, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = local_train_master_image.remove(db, db_obj=db_image)
    return image
