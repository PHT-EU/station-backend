from typing import List

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from station.app.api import dependencies

from station.app.schemas import local_trains
from station.app.crud.local_train_master_image import local_train_master_image

router = APIRouter()


@router.post("", response_model=local_trains.LocalTrainMasterImage)
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


@router.get("/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def get_master_image(image_id: str, db: Session = Depends(dependencies.get_db)):
    image = local_train_master_image.get(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.get("", response_model=List[local_trains.LocalTrainMasterImage])
def list_master_images(db: Session = Depends(dependencies.get_db), skip: int = 0, limit: int = 100, sync: bool = False):
    if sync:
        local_train_master_image.sync_with_harbor(db)
    images = local_train_master_image.get_multi(db, skip=skip, limit=limit)
    return images


@router.put("/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def update_master_image(image_id: str, update_msg: local_trains.LocalTrainMasterImageUpdate,
                        db: Session = Depends(dependencies.get_db)):
    db_image = local_train_master_image.get(db, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = local_train_master_image.update(db, db_obj=db_image, obj_in=update_msg)
    return image


@router.delete("/{image_id}", response_model=local_trains.LocalTrainMasterImage)
def delete_master_image(image_id: str, db: Session = Depends(dependencies.get_db)):
    db_image = local_train_master_image.get(db, image_id)
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    image = local_train_master_image.remove(db, db_obj=db_image)
    return image
