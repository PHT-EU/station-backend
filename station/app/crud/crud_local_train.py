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
from station.app.schemas.local_trains import LocalTrainCreate, LocalTrainUpdate, LocalTrainRunConfig, LocalTrainConfigurationStep
from station.app.trains.local.minio import train_data
from station.app.trains.local.update import update_configuration_status
from station.clients.minio import MinioClient
from station.ctl.constants import DataDirectories


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

    def create_run(self, db: Session, *, obj_in: LocalTrainRunConfig) -> ModelType:
        """
        create a database entry for a local train execution

        @param db: eference to the postgres database
        @param obj_in: LocalTrainRun json as defind in the schemas
        @return: local run object
        """
        run = LocalTrainExecution(train_id=obj_in.train_id,
                                  airflow_dag_run=obj_in.run_id)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def remove_train(self, db: Session, train_id: str) -> ModelType:
        """

        @param db:
        @param train_id:
        @return:
        """
        # TODO remove query results when exist
        # remove minIo entry
        files = self.get_all_uploaded_files(train_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for file in files:
            loop.run_until_complete(train_data.delete_train_file(file.object_name))
        # remove sql database entrys for LocalTrainExecution
        obj = db.query(LocalTrainExecution).filter(LocalTrainExecution.train_id == train_id).all()
        for run in obj:
            db.delete(run)
        db.commit()
        # remove sql database entry for LocalTrain
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()
        if not obj:
            return f"train_id {train_id} dose not exit"
        db.delete(obj[0])
        db.commit()
        return obj

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
        state = update_train.state
        minio_client = MinioClient()
        files = minio_client.get_minio_dir_items(DataDirectories.LOCAL_TRAINS.value, db_obj.id)
        configuration_state = update_configuration_status(update_train, files)
        state.configuration_state = configuration_state
        db.commit()
        return update_train


local_train = CRUDLocalTrain(LocalTrain)
