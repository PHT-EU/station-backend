import uuid
import os
import asyncio
from datetime import datetime
from typing import Union, Any

from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from fastapi.encoders import jsonable_encoder

from station.app.crud.base import CRUDBase, ModelType
from station.app.models.local_trains import LocalTrain, LocalTrainExecution, LocalTrainConfig
from station.app.schemas.local_trains import LocalTrainCreate, LocalTrainUpdate, LocalTrainRun, LocalTrainConfigSchema
from station.app.local_train_minio.LocalTrainMinIO import train_data


class CRUDLocalTrain(CRUDBase[LocalTrain, LocalTrainCreate, LocalTrainUpdate]):
    def create(self, db: Session, *, obj_in: LocalTrainCreate) -> ModelType:
        """
        Create the data base entry for a local train
        @param db: reference to the postgres database
        @param obj_in: LocalTrainCreate json as defined in the schemas
        @return: local train object
        """
        # if no name is given in the local train the uid  is set as train id and train name
        if obj_in is None:
            train_id = str(uuid.uuid4())
            train = LocalTrain(train_id=train_id,
                               train_name=train_id,
                               airflow_config_json=self._create_empty_config(train_id)
                               )
        else:
            train_id = str(uuid.uuid4())
            train = LocalTrain(
                train_id=train_id,
                train_name=obj_in.train_name,
                airflow_config_json=self._create_empty_config(train_id)
            )
        # add and commit the new entry
        db.add(train)
        db.commit()
        db.refresh(train)
        return train

    def create_config(self, db: Session, *, obj_in: LocalTrainConfigSchema) -> ModelType:
        db_config: LocalTrainConfig = db.query(LocalTrainConfig).filter(
            LocalTrainConfig.name == obj_in.name
        ).first()
        if db_config:
            raise HTTPException(status_code=400, detail="A config with the given name already exists.")
        else:
            new_config = LocalTrainConfig(
                name=obj_in.name,
                airflow_config=self._create_config(obj_in))
            db.add(new_config)
            db.commit()
            db.refresh(new_config)
            if obj_in.train_id is not None:
                config_id = new_config.id
                try:
                    db.query(LocalTrain).filter(LocalTrain.train_id == obj_in.train_id).update(
                        {"config_id": config_id})
                    db.query(LocalTrain).filter(LocalTrain.train_id == obj_in.train_id).update(
                        {"updated_at": datetime.now()})
                    db.commit()
                except IndexError as _:
                    raise HTTPException(status_code=404, detail=f"Train with id '{obj_in.train_id}' was not found.")
        return obj_in

    def create_run(self, db: Session, *, obj_in: LocalTrainRun) -> ModelType:
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

    def remove_train(self, db: Session, train_id: str) -> Union[str, Any]:
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
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        if not obj:
            return HTTPException(status_code=404, detail=f"train_id {train_id} dose not exit")
        db.delete(obj)
        db.commit()
        return obj

    def remove_config(self, db: Session, config_name: str):

        config = db.query(LocalTrainConfig).filter(LocalTrainConfig.config_name == config_name).first()
        if not config:
            return HTTPException(status_code=404, detail=f"Config {config_name} dose not exit")
        trains = db.query(LocalTrain).filter(LocalTrain.config_id == config.id).all()
        for train in trains:
            train.update({"config_id": None, "updated_at": datetime.now()})
        db.delete(config)
        db.commit()
        return config

    def remove_config_entry(self, db: Session, train_id: str, key: str):
        """
        set the value of the key in the train config to none

        @param db: reference to the postgres database
        @param train_id:  Id of the train that has to be changed
        @param key: key that will be set to null
        @return: json response about the removel
        """
        config = self.get_config(db, train_id)
        try:
            config[key] = None
            self._update_config(db, train_id, config)
            return config
        except KeyError as e:
            print(e)
            return HTTPException(status_code=404, detail=f"{key} is not a key that can be reset")


    def put_config(self, db: Session, train_id: str, config_name: str):
        train = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        if not train:
            raise HTTPException(status_code=404, detail=f"Train {train} not found")
        config = db.query(LocalTrainConfig).filter(LocalTrain.config_name == config_name).first()
        if not config:
            raise HTTPException(status_code=404, detail=f"Config {config_name} not found")
        train.update({"config_id": config.id, "updated_at": datetime.now()})
        db.commit()
        return config

    def update_config_add_repository(self, db: Session, train_id: str, repository: str):
        """

        @param db:
        @param train_id:
        @param repository:
        @return:
        """
        config = self.get_config(db, train_id)
        harbor_api = os.getenv("HARBOR_URL")
        harbor_url = harbor_api.split("/")[2]
        config["repository"] = f"{harbor_url}/{repository}"
        self._update_config(db, train_id, config)
        return config

    def update_config_add_tag(self, db: Session, train_id: str, tag: str):
        """

        @param db:
        @param train_id:
        @param tag:
        @return:
        """
        config = self.get_config(db, train_id)
        config["tag"] = f"{tag}"
        self._update_config(db, train_id, config)
        return config

    def update_config_add_entrypoint(self, db: Session, train_id: str, entrypoint: str):
        """

        @param db:
        @param train_id:
        @param entrypoint:
        @return:
        """
        config = self.get_config(db, train_id)
        config["entrypoint"] = f"{entrypoint}"
        self._update_config(db, train_id, config)
        return config

    def update_config_add_query(self, db: Session, train_id: str, query: str):
        """

        @param db:
        @param train_id:
        @param query:
        @return:
        """
        config = self.get_config(db, train_id)
        config["query"] = f"{query}"
        self._update_config(db, train_id, config)
        return config

    def _update_config(self, db, train_id, config):
        """

        @param db:
        @param train_id:
        @param config:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        if obj.config_id is not None:
            #obj = db.query(LocalTrainConfig).filter(LocalTrainConfig.id == obj.config_id)
            db.query(LocalTrainConfig).filter(LocalTrainConfig.id == obj.config_id).update({"updated_at": datetime.now()})
            db.query(LocalTrainConfig).filter(LocalTrainConfig.id == obj.config_id).update({"airflow_config": config})
            #obj.update({"airflow_config": config, "updated_at": datetime.now()})
            db.commit()
        else:
            # old with integrated config
            db.query(LocalTrain).filter(LocalTrain.train_id == train_id).update({"updated_at": datetime.now()})
            db.query(LocalTrain).filter(LocalTrain.train_id == train_id).update({"airflow_config_json": config})
            db.commit()

    def get_config(self, db, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        if obj.config_id is not None:
            obj = db.query(LocalTrainConfig).filter(LocalTrainConfig.id == obj.config_id).first()
            config = obj.airflow_config
            return config

        # old with integrated config
        old_config = obj.airflow_config_json
        if old_config is None:
            self._create_empty_config(train_id)
        else:
            return old_config

    def _create_empty_config(self, train_id):
        """

        @param train_id:
        @return:
        """
        return {
            "repository": None,
            "tag": "latest",
            "env": None,
            "query": None,
            "entrypoint": None,
            "volumes": None,
            "train_id": train_id
        }

    async def add_file_minio(self, upload_file: UploadFile, train_id: str):
        """

        @param upload_file:
        @param train_id:
        @return:
        """
        await train_data.store_train_file(upload_file, train_id)

    def get_all_uploaded_files(self, train_id: str):
        """

        @param train_id:
        @return:
        """
        files = train_data.get_all_uploaded_files_train(train_id)
        output_files = []
        for file in files:
            output_files.append(
                {
                    "bucket_name": file.bucket_name,
                    "object_name": file.object_name,
                    "size": file.size,
                    "last_modified": file.last_modified
                }
            )
        return  output_files
    def get_trains(self, db: Session):
        """

        @param db:
        @return:
        """
        trains = db.query(LocalTrain).all()
        return trains

    def get_train_status(self, db: Session, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()
        return obj

    def get_configs(self, db: Session):
        configs = db.query(LocalTrainConfig).all()
        return_configs = []
        for config in configs:
            return_configs.append(config.airflow_config)
        return {"configs" :return_configs}

    def get_train_config(self, db: Session, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        try:
            obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).first()
        except IndexError as _:
            raise HTTPException(status_code=404, detail=f"Train with id '{train_id}' was not found.")
        if obj.config_id is not None:
            obj = db.query(LocalTrainConfig).filter(LocalTrainConfig.id == obj.config_id).first()
            config = obj.airflow_config
            config["train_id"] = train_id
            print("config from extrernal config")

            return config
        config = obj.airflow_config_json
        return config

    def get_train_name(self, db: Session, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()[0]
        train_name = obj.train_name
        return train_name

    def get_train_id(self, db: Session, train_name: str):
        """

        @param db:
        @param train_name:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_name == train_name).all()[0]
        train_id = obj.train_id
        return train_id

    def get_train_logs(self, db: Session, train_id: str):
        """
        Returns the run logs for the runs of the train

        @param db: reference to the postgres database
        @param train_id: Id of the train
        @return: list of logs
        """
        runs = db.query(LocalTrainExecution).filter(LocalTrainExecution.train_id == train_id).all()
        logs = []
        for run in runs:
            run_id = run.airflow_dag_run
            log = {"run_id": run_id,
                   "log": train_data.read_file(f"{train_id}/{run_id}/log.")}
            logs.append(log)
        return logs

    def get_last_train_logs(self, db: Session, train_id: str):
        """
        Returns the run logs for the runs of the train

        @param db: reference to the postgres database
        @param train_id: Id of the train
        @return: log of
        """
        runs = db.query(LocalTrainExecution).filter(LocalTrainExecution.train_id == train_id).all()
        run_id = runs[-1].airflow_dag_run
        log = {"run_id": run_id,
               "log": train_data.read_file(f"{train_id}/{run_id}/log.")}
        return log

    def get_last_run(self, db: Session, train_id: str):
        # TODO get last run id
        runs = db.query(LocalTrainExecution).filter(LocalTrainExecution.train_id == train_id).all()
        print(runs)

    def _create_config(self, obj_in):
        if not isinstance(obj_in, LocalTrainConfigSchema):
            raise HTTPException(status_code=400,
                                detail=f"obj_in is not of type LocalTrainConfigSchema but of type {type(obj_in)}")

        airflow_config = self._create_empty_config(None)
        airflow_config["repository"] = self._get_repository(obj_in.image)
        if obj_in.tag is not None:
            airflow_config["tag"] = obj_in.tag
        else:
            airflow_config["tag"] = "latest"

        airflow_config["query"] = obj_in.query
        airflow_config["entrypoint"] = obj_in.entrypoint
        airflow_config["volumes"] = obj_in.volumes
        airflow_config["env"] = obj_in.env
        return airflow_config

    def _get_repository(self, image: str):
        """

        @param image:
        @return:
        """

        harbor_api = os.getenv("HARBOR_URL")
        harbor_url = harbor_api.split("/")[2]
        return f"{harbor_url}/{image}"


local_train = CRUDLocalTrain(LocalTrain)
