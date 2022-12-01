from loguru import logger

from station.app.settings import Settings
from station.clients.harbor_client import HarborClient
from station.clients.airflow.client import AirflowClient
from station.clients.minio.client import MinioClient
from station.clients.central.central_client import CentralApiClient


class StationClients:
    airflow: AirflowClient
    harbor: HarborClient
    minio: MinioClient
    central: CentralApiClient

    def __init__(self, settings: Settings):
        self.settings = settings

    def initialize(self):
        if not self.settings.is_initialized:
            logger.warning("Station settings are not initialized. Please call settings.setup() before initializing clients.")
            self.settings.setup()
        self.airflow = AirflowClient(
            airflow_api_url=self.settings.config.airflow.api_url,
            airflow_user=self.settings.config.airflow.user,
            airflow_password=self.settings.config.airflow.password,
        )
        self.harbor = HarborClient(
            api_url=self.settings.config.registry.api_url,
            username=self.settings.config.registry.user,
            password=self.settings.config.registry.password.get_secret_value(),
        )

        self.minio = MinioClient(
            minio_server=self.settings.config.minio.server_url,
            access_key=self.settings.config.minio.access_key,
            secret_key=self.settings.config.minio.secret_key,
        )

        self.minio.setup_buckets()

        self.central = CentralApiClient(
            api_url=self.settings.config.central_ui.api_url,
            robot_id=self.settings.config.central_ui.robot_id,
            robot_secret=self.settings.config.central_ui.robot_secret.get_secret_value(),
        )

        # self.minio_client = MinioClient(settings)
