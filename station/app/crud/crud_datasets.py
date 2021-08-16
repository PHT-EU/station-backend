from sqlalchemy.orm import Session
from train_lib.fhir.fhir_client import PHTFhirClient

import asyncio

import pandas as pd

from .base import CRUDBase, CreateSchemaType, ModelType
from fastapi.encoders import jsonable_encoder
from station.app.models.datasets import DataSet
from station.app.schemas.datasets import DataSetCreate, DataSetUpdate
from station.clients.minio import MinioClient


class CRUDDatasets(CRUDBase[DataSet, DataSetCreate, DataSetUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        print(obj_in_data)
        db_obj = self.model(**obj_in_data)
        if obj_in_data["storage_type"] == "minio":
            self._extract_mino_information(db_obj, obj_in_data)
        elif obj_in_data["storage_type"] == "csv":
            self._extract_csv_information(db_obj, obj_in_data)
        elif obj_in_data["storage_type"] == "fhir":
            self._extract_fhir_information(db_obj, obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def _extract_mino_information(self, db_obj, obj_in_data):
        client = MinioClient()
        n_items = len(list(client.get_data_set_items(obj_in_data["access_path"])))
        db_obj.n_items = n_items
        return db_obj

    def _extract_csv_information(self, db_obj, obj_in_data):
        csv_df = pd.read_csv(db_obj.access_path)
        n_items = len(csv_df.index)
        db_obj.n_items = n_items
        if obj_in_data["target_field"] is not None:
            class_distribution = (csv_df[obj_in_data["target_field"]].value_counts()/n_items).to_json()
            db_obj.class_distribution = class_distribution
        return db_obj
    
    def _extract_fhir_information(self, db_obj, obj_in_data):
        # TODO finish when fhir client has the functinalty
        """fhir_client = PHTFhirClient(obj_in_data["access_path"],
                                    obj_in_data["fhir_user"],
                                    obj_in_data["fhir_password"],
                                    server_type=obj_in_data["fhir_server_type"])
        query={
            "query": {
                "resource": "Resource",
                "parameters": [
                    {
                        "variable": "_count",
                        "condition": 6
                    }
                ]
            },
            "data": {
                "output_format": "json",
                "variables": [
                    "total"
                ]
            }
        }
        results = asyncio.run(fhir_client.execute_query(query=query))

        print(results)"""
        pass


datasets = CRUDDatasets(DataSet)
