import uuid

from sqlalchemy.orm import Session

from .base import CRUDBase, CreateSchemaType, ModelType

from station.app.models.local_trains import LocalTrain
from station.app.schemas.local_trains import LocalTrainCreate, LocalTrainUpdate


class CRUDLocalTrain(CRUDBase[LocalTrain, LocalTrainCreate, LocalTrainUpdate]):
    def create(self, db: Session, *, obj_in: LocalTrainCreate) -> ModelType:
        if obj_in == None:
            train = LocalTrain(
                train_id=uuid.uuid4()
            )
        else:
            train = LocalTrain(
                train_id=obj_in.train_id
            )
        db.add(train)
        db.commit()
        db.refresh(train)
        return train

    def get_trains(self, db: Session):
        trains = db.query(LocalTrain).all()
        return trains

    def remove_train(self, db: Session, *, train_id: int) -> ModelType:
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()
        db.delete(obj)
        db.commit()
        return obj


local_train = CRUDLocalTrain(LocalTrain)
