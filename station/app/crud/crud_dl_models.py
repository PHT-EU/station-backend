from typing import Any
from sqlalchemy.orm import Session

from station.app.crud.base import CRUDBase
from station.app.models.dl_models import TorchModel, DLModel
from station.app.schemas.dl_models import TorchModelCreate, TorchModelUpdate, DLModelCreate, DLModelUpdate


class CRUDTorchModel(CRUDBase[TorchModel, TorchModelCreate, TorchModelUpdate]):

    def create_model_for_train(self, db: Session, *, train_id: int, obj_in: TorchModelCreate) -> TorchModel:
        db_model = TorchModel(
            **obj_in.dict(),
            train_id=train_id
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return db_model

    def get_train_model(self, db: Session, *, train_id: int) -> TorchModel:
        db_model = db.query(TorchModel).filter(TorchModel.train_id == train_id).first()
        return db_model

    def get_model_by_model_id(self, db: Session, model_id: str) -> TorchModel:
        db_model = db.query(TorchModel).filter(TorchModel.model_id == model_id).first()
        return db_model

    def create_model_with_id(self, db: Session, model_id: str) -> TorchModel:
        db_model = TorchModel(
            model_id=model_id
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return db_model


class CRUDDLModels(CRUDBase[DLModel, DLModelCreate, DLModelUpdate]):

    def create_dl_model_with_id(self, db: Session, *, model_id: str, obj_in: DLModelCreate) -> DLModel:
        db_dl_model = self.model(
            model_id=model_id,
            **obj_in.dict()
        )
        db.add(db_dl_model)
        db.commit()
        db.refresh(db_dl_model)
        return db_dl_model

    def create_dl_model_for_train(self, db: Session, *, train_id: int, obj_in: DLModelCreate) -> DLModel:
        db_dl_model = self.model(
            train_id=train_id,
            **obj_in.dict()
        )
        db.add(db_dl_model)
        db.commit()
        db.refresh(db_dl_model)
        return db_dl_model

    def get_model_by_model_id(self, db: Session, model_id: str) -> DLModel:
        db_model = db.query(DLModel).filter(DLModel.model_id == model_id).first()
        return db_model

    def get_train_model(self, db: Session, train_id: Any) -> DLModel:
        db_model = db.query(DLModel).filter(DLModel.train_id == train_id).first()
        return db_model

    def create_model_from_conductor(self, db: Session, train_id: Any, model_in: dict):
        db_dl_model = self.model(
            train_id=train_id
        )
        db_dl_model.model_src = model_in["model_src"]
        db_dl_model.model_name = model_in["model_name"]
        db_dl_model.model_type = model_in["model_type"]
        db.add(db_dl_model)
        db.commit()
        db.refresh(db_dl_model)
        return db_dl_model


torch_models = CRUDTorchModel(TorchModel)

dl_models = CRUDDLModels(DLModel)
