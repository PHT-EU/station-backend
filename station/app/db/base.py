# Import all the models, so that Base has them before being
# imported by Alembic
# ruff: noqa
from station.app.db.base_class import Base  # noqa

from station.app.models.docker_trains import (
    DockerTrainConfig,
    DockerTrain,
    DockerTrainState,
    DockerTrainExecution,
)  # noqa
from station.app.models.datasets import DataSet  # noqa
from station.app.models.fhir_server import FHIRServer  # noqa
from station.app.models.discovery import DataSetSummary  # noqa
from station.app.models.notification import Notification
from station.app.models.local_trains import (
    LocalTrain,
    LocalTrainConfig,
    LocalTrainState,
    LocalTrainExecution,
    LocalTrainMasterImage,
)  # noqa

# from station.app.models.user import User  # noqa
