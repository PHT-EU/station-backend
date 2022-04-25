from sqlalchemy.orm import Session
import pandas as pd

from .base import CRUDBase, CreateSchemaType, ModelType, Optional, Any
from fastapi.encoders import jsonable_encoder
from station.app.models.datasets import DataSet
from station.app.schemas.datasets import DataSetCreate, DataSetUpdate, DataSetStatistics
from station.app.datasets.filesystem import get_file


class CRUDDatasets(CRUDBase[DataSet, DataSetCreate, DataSetUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> Optional[ModelType]:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        try:
            file = get_file(db_obj.access_path)
        except:
            raise FileNotFoundError
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def get_data(self, db: Session, data_set_id):
        dataset = self.get(db, data_set_id)
        if dataset.data_type == "image":
            pass
        elif dataset.data_type == "csv":
            path = dataset.access_path
            file = get_file(path)
            with file as f:
                csv_df = pd.read_csv(f)
                return csv_df
        elif dataset.data_type == "directory":
            pass
        elif dataset.data_type == "fhir":
            pass
        return dataset

    def get_by_name(self, db: Session, name: str):
        dataset = db.query(self.model).filter(self.model.name == name).first()
        return dataset


datasets = CRUDDatasets(DataSet)
