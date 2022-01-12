import json
import os
from typing import Union, Optional, Tuple
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
    AUTH_SERVER_HOST = "AUTH_SERVER_URL"
    AUTH_SERVER_PORT = "AUTH_SERVER_PORT"
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
    host: Optional[AnyHttpUrl] = "station-auth"
    port: Optional[int] = 3010


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
    fernet_key: Optional[SecretStr] = None
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

        logger.info(f"Station backend setup successful {Emojis.SUCCESS}")
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
        self._setup_station_auth()
        self._setup_registry_connection()

    def _setup_station_auth(self):

        logger.info(f"{Emojis.INFO}Setting up station authentication...")

        # check if station auth is configured via environment variables
        env_auth_server, env_auth_port, env_auth_robot, env_auth_robot_secret = self._get_auth_env_vars()

        _auth_server = False
        # ensure there is an auth server specified in production mode
        if not (env_auth_server and env_auth_robot and env_auth_robot_secret) or self.config.auth:
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   No station auth specified in config or env vars,"
                                 f" invalid configuration for production")

        # no auth config present at initialization, create a new one
        elif not self.config.auth and (env_auth_server and env_auth_robot and env_auth_robot_secret):
            logger.debug(f"{Emojis.INFO}No auth config found, creating new one from env vars.")
            env_auth_config = AuthConfig(
                host=env_auth_server,
                port=env_auth_port,
                robot_id=env_auth_robot,
                robot_secret=env_auth_robot_secret
            )

            self.config.auth = env_auth_config
            _auth_server = True
        # if config and env vars exist override the config values with the environment variables
        elif self.config.auth and (env_auth_server or env_auth_robot or env_auth_robot_secret or env_auth_port):
            logger.debug(f"Overriding auth server config with env var specifications.")
            if env_auth_server:
                self.config.auth.host = env_auth_server
            if env_auth_port:
                self.config.auth.port = env_auth_port
            if env_auth_robot:
                self.config.auth.robot_id = env_auth_robot
            if env_auth_robot_secret:
                self.config.auth.robot_secret = env_auth_robot_secret
            # validate the overridden config
            self.config.auth = AuthConfig(**self.config.auth.dict())
            _auth_server = True

        # log authentication server config and status
        if _auth_server:
            logger.info(f"Auth server: url - {self.config.auth.host}:{self.config.auth.port},"
                        f" robot - {self.config.auth.robot_id}")
        else:
            logger.warning(f"{Emojis.WARNING}No auth server specified in config or env vars,"
                           f" ignoring in development mode")

    def _setup_registry_connection(self):
        logger.info(f"Setting up registry connection...")
        env_registry, env_registry_user, env_registry_password = self._get_registry_env_vars()

        # catch attribute error if no registry config is present in config
        try:
            registry_config = self.config.registry
        except AttributeError:
            registry_config = None
        _registry_config = False
        # override registry config if env vars are present and validate afterwards
        if registry_config and (env_registry and env_registry_user and env_registry_password):
            logger.debug(f"Overriding registry config with env var specifications.")
            if env_registry:
                registry_config.address = env_registry
            if env_registry_user:
                registry_config.user = env_registry_user
            if env_registry_password:
                registry_config.password = env_registry_password
            # validate the overridden config
            registry_config = RegistrySettings(**registry_config.dict())
        # no registry config found
        elif not registry_config and not (env_registry and env_registry_user and env_registry_password):
            _registry_config = False
        elif not registry_config and (env_registry and env_registry_user and env_registry_password):
            logger.debug(f"{Emojis.INFO}No registry config found, creating new one from env vars.")
            registry_config = RegistrySettings(
                address=env_registry,
                user=env_registry_user,
                password=env_registry_password
            )
            self.config.registry = registry_config
        # log registry config and status
        if registry_config:
            logger.info(f"Registry: url - {self.config.registry.address}, user - {self.config.registry.user}")
        else:
            # raise error if no registry is configured in production mode
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   No registry config specified in config or env vars")
            else:
                logger.warning(f"No registry config specified in config or env vars, ignoring in development mode")

    def _get_registry_env_vars(self) -> Tuple[str, str, str]:
        env_registry = os.getenv(StationEnvironmentVariables.REGISTRY_URL.value)
        env_registry_user = os.getenv(StationEnvironmentVariables.REGISTRY_USER.value)
        env_registry_password = os.getenv(StationEnvironmentVariables.REGISTRY_PW.value)
        return env_registry, env_registry_user, env_registry_password

    @staticmethod
    def _get_auth_env_vars() -> Tuple[str, str, str, str]:
        env_auth_server = os.getenv(StationEnvironmentVariables.AUTH_SERVER_HOST.value)
        env_auth_port = os.getenv(StationEnvironmentVariables.AUTH_SERVER_PORT.value)
        if env_auth_port:
            env_auth_port = int(env_auth_port)
        env_auth_robot = os.getenv(StationEnvironmentVariables.AUTH_ROBOT_ID.value)
        env_auth_robot_secret = os.getenv(StationEnvironmentVariables.AUTH_ROBOT_SECRET.value)

        return env_auth_server, env_auth_port, env_auth_robot, env_auth_robot_secret

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

    def _check_env_var_and_replace_config_attr(self, env_var: StationEnvironmentVariables, config_attr: str):
        pass


settings = Settings()
