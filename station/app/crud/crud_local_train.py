import uuid
import os
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile


from station.app.crud.base import CRUDBase, ModelType
from station.app.models.local_trains import LocalTrain, LocalTrainExecution
from station.app.schemas.local_trains import LocalTrainCreate, LocalTrainUpdate, LocalTrainRun
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
            id = str(uuid.uuid4())
            train = LocalTrain(train_id=id,
                               train_name=id,
                               airflow_config_json=self._create_emty_config(id)
                               )
        else:
            train_id = str(uuid.uuid4())
            train = LocalTrain(
                train_id=train_id,
                train_name=obj_in.train_name,
                airflow_config_json=self._create_emty_config(train_id)
            )
        # add and commit the new entry
        db.add(train)
        db.commit()
        db.refresh(train)
        return train

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
            return f"{key} was removed"
        except KeyError as e:
            print(e)
            return f"{key} is not a key that can be reset"

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
        db.query(LocalTrain).filter(LocalTrain.train_id == train_id).update({"updated_at": datetime.now()})
        db.query(LocalTrain).filter(LocalTrain.train_id == train_id).update({"airflow_config_json": config})
        db.commit()

    def get_config(self, db, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()[0]
        old_config = obj.airflow_config_json
        if old_config is None:
            self._create_emty_config(train_id)
        else:
            return old_config

    def _create_emty_config(self, train_id):
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
        return train_data.get_all_uploaded_files_train(train_id)

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

    def get_train_config(self, db: Session, train_id: str):
        """

        @param db:
        @param train_id:
        @return:
        """
        obj = db.query(LocalTrain).filter(LocalTrain.train_id == train_id).all()[0]
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


local_train = CRUDLocalTrain(LocalTrain)
