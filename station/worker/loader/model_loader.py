import importlib.machinery
import importlib.util
import os
import tempfile
from typing import Any

import requests
from conductor_lib.src.torch import LightningTrainModel
from sqlalchemy.orm import Session

from station.app.crud import federated_trains
from station.common.clients.minio import MinioClient


class ModelLoader:
    def __init__(self, station_url: str = None):
        self.station_url = station_url if station_url else os.getenv("STATION_API_URL")
        assert self.station_url
        self.minio_client = MinioClient()

    def get_model_from_station(self, model_id: str = None) -> LightningTrainModel:
        """
        Use the station api to get a model registered under the specified model_id and return the initialized model

        :param model_id: identifier of model registered at a station
        :return: initialized model instance stored in the db with model_id
        """

        if not model_id:
            model_id = self.model_id

        # Get the model from the station api
        url = self.station_url + f"/api/station/models/{model_id}"

        r = requests.get(url=url)

        r.raise_for_status()
        model = r.json()
        # initialize the model based on the received src code and name
        model = self._make_lightning_module(model["model_src"], model["model_name"])
        return model

    def load_train_model(self, db: Session, train_id: Any):
        db_train = federated_trains.get_by_train_id(db=db, train_id=train_id)

        model = db_train.model
        assert model

        lightning_module = self._make_lightning_module(
            model.model_src, module_name=model.model_name
        )
        return lightning_module

    def save_model_checkpoint(self):
        # TODO
        pass

    def load_torch_model_from_json(
        self, model_json: dict = None
    ) -> LightningTrainModel:
        """
        Parse the content relevant for initializing a model from the given dictionary containing a user submitted
        json file defining the module.
        Initialize the model based on the found definitions.

        :param model_json: submitted json object
        :return: initialized instance of a LightningTrainModel
        """
        lightning_model_name = model_json["objects"]["lightning_model"]
        lightning_model_src = model_json["src"]["lightning_model"]

        ligntning_module = self._make_lightning_module(
            lightning_model_src, lightning_model_name
        )
        return ligntning_module

    @staticmethod
    def _make_lightning_module(src: str, module_name: str) -> LightningTrainModel:
        """
        Creates a temporary python file based on the src code string submitted using a client library.
        The lightning train model specified by module_name is imported and initialized from the created module and
        returned as an in memory object.

        :param src: String containing the source definition of the model
        :param module_name: the name of the model to be imported from src
        :return: an initialized LightningTrainModel instance based on the submitted source code
        """

        # intialize a tempfile with the model source code
        tmp_mod = tempfile.NamedTemporaryFile("w+b", suffix=".py", delete=False)
        tmp_mod.write(src.encode())
        tmp_mod.read()

        # initialize the temp file as a python module
        spec = importlib.util.spec_from_file_location("lightning_model", tmp_mod.name)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)

        # Get the model by its name and initialize it
        model: LightningTrainModel = foo.__getattribute__(module_name)()

        # cleanup
        tmp_mod.close()
        os.unlink(tmp_mod.name)

        return model
