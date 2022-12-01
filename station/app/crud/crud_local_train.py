import uuid
import os
import asyncio
from datetime import datetime
from typing import Union, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from station.app.crud.base import CRUDBase, ModelType, CreateSchemaType, UpdateSchemaType
from station.app.models.local_trains import LocalTrain, LocalTrainExecution, LocalTrainState, LocalTrainMasterImage
from station.app.schemas.local_trains import LocalTrainCreate, LocalTrainUpdate, LocalTrainRunConfig, \
    LocalTrainConfigurationStep
from station.app.trains.local.minio import train_data
from station.app.trains.local.update import update_configuration_status
from station.clients.minio import MinioClient
from station.ctl.constants import DataDirectories
from station.app.config import clients



class CRUDLocalTrain(CRUDBase[LocalTrain, LocalTrainCreate, LocalTrainUpdate]):

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in, exclude_none=True)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        train = self.create_initial_state(db, db_obj)
        state = train.state
        state.configuration_state = LocalTrainConfigurationStep.initialized.value
        db.commit()

        return train

    def create_run(self, db: Session, *, train_id: str, dag_run: str,
                   config_id: int = None, dataset_id: str = None) -> LocalTrainExecution:
        """
        create a database entry for a local train execution

        @param db: eference to the postgres database
        @param obj_in: LocalTrainRun json as defind in the schemas
        @return: local run object
        """
        run = LocalTrainExecution(
            train_id=train_id,
            airflow_dag_run=dag_run,
            config_id=config_id,
            dataset_id=dataset_id,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    async def remove_train(self, db: Session, train_id: str) -> ModelType:
        """

        @param db:
        @param train_id:
        @return:
        """
        # TODO remove query results when exist
        # remove files stored in minio
        minio_client = MinioClient()
        minio_client.delete_folder(bucket=str(DataDirectories.LOCAL_TRAINS.value), directory=train_id)

        # remove sql database entries for LocalTrainExecution
        obj = db.query(LocalTrainExecution).filter(LocalTrainExecution.train_id == train_id).all()
        for run in obj:
            db.delete(run)
        db.commit()
        # remove sql database entry for LocalTrain
        db_train = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        db.delete(db_train)
        db.commit()
        return db_train

    def create_initial_state(self, db: Session, db_obj: LocalTrain):
        state = LocalTrainState(
            train_id=db_obj.id
        )
        db.add(state)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        update_train = super().update(db, db_obj=db_obj, obj_in=obj_in)
        update_train.updated_at = datetime.now()
        db.commit()
        state = update_train.state
        minio_client = MinioClient()
        files = minio_client.get_minio_dir_items(DataDirectories.LOCAL_TRAINS.value, db_obj.id)
        configuration_state = update_configuration_status(update_train, files)
        state.configuration_state = configuration_state
        db.commit()
        return update_train


local_train = CRUDLocalTrain(LocalTrain)
