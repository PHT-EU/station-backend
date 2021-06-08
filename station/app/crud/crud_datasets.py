from sqlalchemy.orm import Session

from .base import CRUDBase, CreateSchemaType, ModelType
from fastapi.encoders import jsonable_encoder
from station.app.models.data import DataSet
from station.app.schemas.datasets import DataSetCreate, DataSetUpdate
from station.clients.minio import MinioClient


class CRUDDatasets(CRUDBase[DataSet, DataSetCreate, DataSetUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        if obj_in_data["storage_type"] == "minio":
            client = MinioClient()
            n_items = len(list(client.get_data_set_items(obj_in_data["access_path"])))
            db_obj.n_items = n_items

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


datasets = CRUDDatasets(DataSet)
