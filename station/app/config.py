import json
import os
from typing import Union, Optional
from cryptography.fernet import Fernet
from pydantic import BaseModel, AnyHttpUrl, SecretStr
from enum import Enum
from loguru import logger

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
    STATION_API_HOST = "STATION_API_HOST"
    STATION_API_PORT = "STATION_API_PORT"
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
    host: Optional[Union[AnyHttpUrl, str]] = os.getenv(StationEnvironmentVariables.STATION_API_HOST.value, "127.0.0.1")
    port: Optional[int] = os.getenv(StationEnvironmentVariables.STATION_API_PORT.value, 8001)
    environment: Optional[StationRuntimeEnvironment] = StationRuntimeEnvironment.PRODUCTION
    fernet_key: Optional[SecretStr] = os.getenv("FERNET_KEY")
    registry: RegistrySettings
    auth: Optional[AuthConfig] = None

    @classmethod
    def from_file(cls, path: str) -> "StationConfig":
        pass


# Evaluation for initialization of values file -> environment
class Settings:
    config: StationConfig
    config_path: Optional[str]

    def __init__(self, config_path: str = None):
        # todo remove dotenv
        load_dotenv(find_dotenv())
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.getenv(StationEnvironmentVariables.CONFIG_PATH.value, "station_config.yaml")

        self._config_file = False
        # self.setup()
        # todo create/update config file

    def setup(self) -> StationConfig:
        logger.info(f"{Emojis.INFO}Setting up station backend...")
        # check for config file at given or default path and load if exists
        self._check_config_path()
        # validate the runtime environment
        self._setup_runtime_environment()
        self._parse_station_environment_variables()

        return self.config

    def get_fernet(self) -> Fernet:
        if self.config.fernet_key is None:
            raise ValueError("No Fernet key provided")

        key = str(self.config.fernet_key)
        return Fernet(key.encode())

    def _check_config_path(self):
        logger.info(f"{Emojis.INFO}Looking for config file...")
        if not os.path.isfile(self.config_path):
            if self.config_path == "station_config.yaml":
                logger.warning(
                    f"\t{Emojis.WARNING}No config file found. "
                    f"Creating default at {os.getcwd() + os.sep + self.config_path}")
            else:
                raise FileNotFoundError(f"{Emojis.ERROR}   Custom config file not found at {self.config_path}.")
            # construct a placeholder config to fill with environment and default values
            self.config = StationConfig.construct()
        # Parse the config file
        else:
            logger.info(f"\t{Emojis.SUCCESS}   Config file found at {self.config_path} loading... ")
            config = StationConfig.from_file(self.config_path)
            self.config = config
            logger.info(f"{Emojis.SUCCESS.value} Config loaded.")

    def _setup_runtime_environment(self):
        environment_var = os.getenv(StationEnvironmentVariables.ENVIRONMENT.value)
        # if config variable is in environment variables use it
        if environment_var:
            try:
                runtime_environment = StationRuntimeEnvironment(environment_var)
                # display when config variable is overwritten with env var
                if self.config.environment:
                    logger.debug(f"{Emojis.INFO}Overriding runtime environment with env var specification.")
            except ValueError as e:
                raise ValueError(f"{Emojis.ERROR}   Invalid value ({environment_var}) for runtime environment"
                                 f" in env var {StationEnvironmentVariables.ENVIRONMENT.value}.")
        # otherwise, use the value parse from config file
        else:
            runtime_environment = self.config.environment

        # Display runtime environment
        if runtime_environment == StationRuntimeEnvironment.PRODUCTION:
            logger.info(f"{Emojis.INFO}Running in production environment.")
        elif runtime_environment == StationRuntimeEnvironment.DEVELOPMENT:
            logger.warning(
                f"{Emojis.WARNING}Development environment detected,"
                f" set environment variable '{StationEnvironmentVariables.ENVIRONMENT.value}' "
                f"to '{StationRuntimeEnvironment.PRODUCTION.value}' for production mode.")
        # set the parsed runtime environment
        self.config.environment = runtime_environment

    def _parse_station_environment_variables(self):

        # ensure that the station id is set
        env_station_id = os.getenv(StationEnvironmentVariables.STATION_ID.value)

        if not env_station_id:
            try:
                # todo improve this
                station_id = self.config.station_id
            except AttributeError:
                raise ValueError(f"{Emojis.ERROR}   No station id specified in config or env var "
                                 f"{StationEnvironmentVariables.STATION_ID.value}.")
        elif env_station_id:
            logger.debug(f"\t{Emojis.INFO}Overriding station id with env var specification.")
            self.config.station_id = env_station_id

        self._setup_station_api()
        self._setup_fernet()

    def _setup_station_api(self):
        # Try to find api host and port in environment variables
        env_station_host = os.getenv(StationEnvironmentVariables.STATION_API_HOST.value)
        if env_station_host:
            logger.debug(f"\t{Emojis.INFO}Overriding station api host with env var specification.")
            self.config.host = env_station_host
        env_station_port = os.getenv(StationEnvironmentVariables.STATION_API_PORT.value)
        if env_station_port:
            logger.debug(f"\t{Emojis.INFO}Overriding station api port with env var specification.")
            self.config.port = int(env_station_port)

    def _setup_fernet(self):
        env_fernet_key = os.getenv(StationEnvironmentVariables.FERNET_KEY.value)
        if not env_fernet_key and not self.config.fernet_key:
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   No fernet key specified in config or env vars.")
            elif self.config.environment == StationRuntimeEnvironment.DEVELOPMENT:
                logger.warning(f"\t{Emojis.WARNING}No fernet key specified in config or env vars")
                logger.info(f"\t{Emojis.INFO}Generating new key for development environment...")
                self.config.fernet_key = Fernet.generate_key().decode()
                logger.info(Emojis.SUCCESS.value + f"New key generated.")
        elif env_fernet_key and self.config.fernet_key:
            logger.debug(f"\t{Emojis.INFO}Overriding fernet key with env var specification.")
            self.config.fernet_key = env_fernet_key

        elif env_fernet_key:
            self.config.fernet_key = env_fernet_key


settings = Settings()
