import json
import os
from typing import Union, Optional
from cryptography.fernet import Fernet
from pydantic import BaseModel, AnyHttpUrl, SecretStr
from enum import Enum

from dotenv import load_dotenv, find_dotenv


class Emojis(str, Enum):
    """
    Enum of emojis to use in the app.
    """
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"


class StationEnvironmentVariables(Enum):
    # station configuration variables
    STATION_ID = "STATION_ID"
    ENVIRONMENT = "ENVIRONMENT"
    FERNET_KEY = "FERNET_KEY"
    STATION_DB_URL = "STATION_DB"
    STATION_DATA_DIR = "STATION_DATA_DIR"
    CONFIG_PATH = "STATION_CONFIG_PATH"

    # auth environment variables
    AUTH_SERVER_URL = "AUTH_SERVER_URL"
    AUTH_ROBOT_ID = "AUTH_ROBOT_ID"
    AUTH_ROBOT_SECRET = "AUTH_ROBOT_SECRET"

    # Registry environment variables
    REGISTRY_URL = "HARBOR_URL"
    REGISTRY_USER = "HARBOR_USER"
    REGISTRY_PW = "HARBOR_PW"

    # minio environment variables
    MINIO_URL = "MINIO_URL"
    MINIO_USER = "MINIO_USER"
    MINIO_PW = "MINIO_PW"


class RegistrySettings(BaseModel):
    address: AnyHttpUrl
    user: str
    password: SecretStr


class AirflowSettings(BaseModel):
    host: Union[AnyHttpUrl, str] = "airflow"
    port: Optional[int] = 8080
    user: Optional[str] = "admin"
    password: Optional[SecretStr] = "admin"


class AuthConfig(BaseModel):
    robot_id: str
    robot_secret: SecretStr
    auth_server_host: Optional[AnyHttpUrl] = "station-auth"
    auth_server_port: Optional[int] = 3010


class StationRuntimeEnvironment(str, Enum):
    """
    Enum of the runtime environments of the station.
    """
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class StationConfig(BaseModel):
    station_id: Union[int, str]
    host: Optional[Union[AnyHttpUrl, str]] = os.getenv("STATION_HOST", "127.0.0.1")
    port: Optional[int] = os.getenv("STATION_PORT", 8001)
    environment: Optional[StationRuntimeEnvironment] = StationRuntimeEnvironment.PRODUCTION
    fernet_key: Optional[SecretStr] = os.getenv("FERNET_KEY")
    registry: RegistrySettings
    auth: Optional[AuthConfig] = None
    developer_mode: bool = False

    @classmethod
    def from_yaml(cls) -> "StationConfig":
        pass


# Evaluation for initialization of values file -> environment
class Settings:
    config: StationConfig
    config_path: Optional[str]

    def __init__(self, config_path: str = None):
        # todo remove dotenv
        load_dotenv(find_dotenv())
        print(f"{Emojis.INFO}Setting up station...")
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.getenv(StationEnvironmentVariables.CONFIG_PATH.value, "station_config.yaml")

        self._config_file = False
        self._check_config_path()
        self._setup_runtime_environment()
        self._parse_environment_to_config()

    @classmethod
    def from_env(cls) -> 'Settings':
        print(f"{Emojis.INFO}Loading environment variables...")

    def parse_config_file(self) -> 'Settings':
        file_type = self.config_path.split('.')[-1]
        if file_type.lower() == 'json':
            json_config = json.loads(open(self.config_path).read())
            self.config = StationConfig(**json_config)

        elif file_type.lower() in ['yaml', "yml"]:
            pass

    def get_fernet(self) -> Fernet:
        if self.config.fernet_key is None:
            raise ValueError("No Fernet key provided")

        key = str(self.config.fernet_key)
        return Fernet(key.encode())

    def _check_config_path(self):
        print(f"{Emojis.INFO}Looking for config file...")
        if not os.path.isfile(self.config_path):
            if self.config_path == "station_config.yaml":
                print(
                    f"\t{Emojis.WARNING}No config file found. "
                    f"Creating default at {os.getcwd() + '/' + self.config_path}")
            else:
                raise FileNotFoundError(f"{Emojis.ERROR}   Custom config file not found at {self.config_path}.")
            # construct a placeholder config to fill with environment and default values
            self.config = StationConfig.construct()
        # Parse the config file

        else:
            print(f"\t{Emojis.SUCCESS}   Config file found at {self.config_path}.")
            self._config_file = True
            config = StationConfig.from_file(self.config_path)
            self.config = config

    def _setup_runtime_environment(self):
        environment = os.getenv(StationEnvironmentVariables.ENVIRONMENT.value)
        if environment:
            if environment == StationRuntimeEnvironment.DEVELOPMENT.value:
                environment_var = StationEnvironmentVariables.ENVIRONMENT.value
                print(
                    f"{Emojis.WARNING}Development environment detected,"
                    f" set environment variable {environment_var} to 'production' for production mode.")
            elif environment == StationRuntimeEnvironment.PRODUCTION.value:
                print(f"{Emojis.INFO}Running in production environment.")
            else:
                raise ValueError(f"{Emojis.ERROR}   Invalid value ({environment}) for environment"
                                 f" in env var {StationEnvironmentVariables.ENVIRONMENT.value}.")

            self.config.environment = StationRuntimeEnvironment(environment)

    def _parse_environment_to_config(self):
        pass


settings = Settings()
