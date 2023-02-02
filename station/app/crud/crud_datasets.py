import json
from typing import List, Union

import pandas as pd
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from station.app.datasets.filesystem import get_file
from station.app.models.datasets import DataSet
from station.app.schemas.datasets import DataSetCreate, DataSetStatistics, DataSetUpdate

from .base import CreateSchemaType, CRUDBase, ModelType


class CRUDDatasets(CRUDBase[DataSet, DataSetCreate, DataSetUpdate]):

    # TODO fix MinIO Client connection
    # using the .create function from the base CRUD operators
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        # TODO check for multiple files
        # try:
        #     file = get_file(db_obj.access_path, db_obj.storage_type)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def get_data(
        self, db: Session, data_set_id: str, file_name: Union[str, List[str]] = None
    ):
        dataset = self.get(db, data_set_id)
        if dataset.data_type == "image":
            raise NotImplementedError
        elif dataset.data_type == "csv":
            path = dataset.access_path
            file = get_file(path, dataset.storage_type)
            with file as f:
                csv_df = pd.read_csv(f)
                return csv_df
        elif dataset.data_type == "directory":
            raise NotImplementedError
        elif dataset.data_type == "fhir":
            raise NotImplementedError
        return dataset

    def get_by_name(self, db: Session, name: str):
        dataset = db.query(self.model).filter(self.model.name == name).first()
        return dataset

    def add_stats(
        self,
        db: Session,
        data_set_id: str,
        stats: DataSetStatistics,
        file_name: str = None,
    ):
        dataset = self.get(db, data_set_id)

        if file_name:
            if dataset.summary:
                stored_stats = json.loads(dataset.summary)
            else:
                stored_stats = {}
            stored_stats[file_name] = stats
            dataset.summary = jsonable_encoder(stored_stats)
        else:
            stats = jsonable_encoder(stats)
            stats_json = json.dumps(stats)
            dataset.summary = stats_json
        db.commit()
        db.refresh(dataset)
        return dataset


datasets = CRUDDatasets(DataSet)
