import os
from typing import Any

from dotenv import find_dotenv, load_dotenv
from sqlalchemy.orm import Session

from station.app.crud import federated_trains
from station.clients.conductor import ConductorRESTClient
from station.clients.minio import MinioClient
from station.worker import SessionLocal
from station.worker.discovery import perform_discovery
from station.worker.loader import BaseLoader, MinioFolderDS, ModelLoader
from station.worker.trainer import FederatedTrainer


class PHTWorker:

    def __init__(self):
        self.conductor_client = ConductorRESTClient()
        self.minio_client = MinioClient()

    def perform_discovery(self, db: Session, train_id: Any):
        db_train = federated_trains.get_by_train_id(db=db, train_id=train_id)
        assert db_train.dataset
        discovery_result = perform_discovery(db_train.dataset)

        discovery_post = {
            "station_id": os.getenv("STATION_ID"),
            "results": discovery_result
        }
        self.conductor_client.post_discovery_results(train_id=train_id, discovery_results=discovery_post)

    def make_data_loader(self, db: Session, train_id: Any):
        db_train = federated_trains.get_by_train_id(db=db, train_id=train_id)
        assert db_train.dataset
        # TODO get configuration setting on whether to load and store the data set/loader
        ds = MinioFolderDS(self.minio_client, data_set_id=db_train.dataset.access_path)
        loader = BaseLoader(data_set=ds).make_data_loader()

        return loader

    def train_model(self, db: Session, train_id: Any):
        model = ModelLoader().load_train_model(db, train_id)
        print(model)
        data_loader = self.make_data_loader(db, train_id)
        trainer = FederatedTrainer(gpus=1, max_epochs=1)
        trainer.fit(model=model, train_dataloader=data_loader)

    def distribute_model(self, db: Session, train_id: Any):
        pass


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    session = SessionLocal()
    TRAIN_ID = "1"
    worker = PHTWorker()
    # worker.perform_discovery(session, TRAIN_ID)
    # loader = worker.make_data_loader(session, TRAIN_ID)
    worker.train_model(session, TRAIN_ID)

    # for i, batch in enumerate(loader):
    #     x, y = batch
    #     print(y, x)
    #     print(x.shape)
    #     if i > 3:
    #         break
