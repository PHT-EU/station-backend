import json
import os
from typing import Union, Optional, Tuple
from cryptography.fernet import Fernet
from pydantic import BaseModel, AnyHttpUrl, SecretStr, AnyUrl
from enum import Enum
from loguru import logger
from yaml import safe_dump, safe_load

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
    STATION_DB = "STATION_DB"
    STATION_API_HOST = "STATION_API_HOST"
    STATION_API_PORT = "STATION_API_PORT"
    FERNET_KEY = "FERNET_KEY"
    STATION_DATA_DIR = "STATION_DATA_DIR"
    CONFIG_PATH = "STATION_CONFIG_PATH"

    # airflow environment variables
    AIRFLOW_HOST = "AIRFLOW_HOST"
    AIRFLOW_PORT = "AIRFLOW_PORT"
    AIRFLOW_USER = "AIRFLOW_USER"
    AIRFLOW_PW = "AIRFLOW_PW"

    # auth environment variables
    AUTH_SERVER_HOST = "AUTH_SERVER_HOST"
    AUTH_SERVER_PORT = "AUTH_SERVER_PORT"
    AUTH_ROBOT_ID = "AUTH_ROBOT_ID"
    AUTH_ROBOT_SECRET = "AUTH_ROBOT_SECRET"

    # Registry environment variables
    REGISTRY_URL = "HARBOR_URL"
    REGISTRY_USER = "HARBOR_USER"
    REGISTRY_PW = "HARBOR_PW"

    # minio environment variables
    MINIO_HOST = "MINIO_HOST"
    MINIO_PORT = "MINIO_PORT"
    MINIO_ACCESS_KEY = "MINIO_ACCESS_KEY"
    MINIO_SECRET_KEY = "MINIO_SECRET_KEY"


class RegistrySettings(BaseModel):
    address: AnyHttpUrl
    user: str
    password: SecretStr


class AirflowSettings(BaseModel):
    host: Union[AnyHttpUrl, str] = "airflow"
    port: Optional[int] = 8080
    user: Optional[str] = "admin"
    password: Optional[SecretStr] = "admin"


class MinioSettings(BaseModel):
    host: Union[AnyHttpUrl, AnyUrl, str]
    port: Optional[int] = 9000
    access_key: Optional[str] = "admin"
    secret_key: Optional[SecretStr] = "admin"


class CentralUISettings(BaseModel):
    api_url: AnyHttpUrl
    client_id: Optional[str] = "admin"
    client_secret: Optional[SecretStr] = "admin"


class AuthConfig(BaseModel):
    robot_id: str
    robot_secret: SecretStr
    host: Optional[Union[AnyHttpUrl, AnyUrl, str]] = "station-auth"
    port: Optional[int] = 3010


class StationRuntimeEnvironment(str, Enum):
    """
    Enum of the runtime environments of the station.
    """
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class StationConfig(BaseModel):
    """
    Object containing the configuration of the station.
    """
    station_id: Union[int, str]
    host: Optional[Union[AnyHttpUrl, str]] = os.getenv(StationEnvironmentVariables.STATION_API_HOST.value, "127.0.0.1")
    port: Optional[int] = os.getenv(StationEnvironmentVariables.STATION_API_PORT.value, 8001)
    db: Optional[SecretStr] = "sqlite:///./app.db"
    environment: Optional[StationRuntimeEnvironment] = StationRuntimeEnvironment.PRODUCTION
    fernet_key: Optional[SecretStr] = None
    registry: RegistrySettings
    auth: Optional[AuthConfig] = None
    airflow: Optional[AirflowSettings] = None
    minio: Optional[MinioSettings] = None
    central_ui: Optional[CentralUISettings] = None

    @classmethod
    def from_file(cls, path: str) -> "StationConfig":
        with open(path, "r") as f:
            return cls(**safe_load(f))

    def to_file(self, path: str) -> None:
        # todo get secret values recursively
        with open(path, "w") as f:
            safe_dump(json.loads(self.json(indent=2)), f)


# Evaluation for initialization of values file < environment
class Settings:
    """
    Class to handle the settings of the station API and connections to other services. Can be configured via a file or
    environment variables.
    """
    config: StationConfig
    config_path: Optional[str]

    def __init__(self, config_path: str = None):
        load_dotenv(find_dotenv())
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = os.getenv(StationEnvironmentVariables.CONFIG_PATH.value, "station_config.yaml")

        self._config_file = False
        # todo create/update config file

    def setup(self) -> StationConfig:
        """
        Initialize the settings. First tries to load the settings from the config file. Then tries to load the settings
        from the environment variables. If a conflicting value is found the environment variable has precedence. If both
        fail, the default settings are used.

        Returns:
            StationConfig The initialized settings.

        """
        logger.info(f"{Emojis.INFO}Setting up station backend...")
        # check for config file at given or default path and load if exists
        self._check_config_path()
        # validate the runtime environment
        self._setup_runtime_environment()
        self._setup_station_environment()

        logger.info(f"Station backend setup successful {Emojis.SUCCESS}")
        return self.config

    def get_fernet(self) -> Fernet:
        """
        Get the Fernet key for encryption and decryption of secrets. Configured via environment variables or station
        config.

        Returns: A fernet object that can be used to encrypt and decrypt secrets.
        """
        if self.config.fernet_key is None:
            raise ValueError("No Fernet key provided")

        key = str(self.config.fernet_key)
        return Fernet(key.encode())

    def _check_config_path(self):
        """
        Checks if a config is present at the given path. Raise an error if custom config file is given but not present.

        Returns:

        """
        logger.info(f"{Emojis.INFO}Looking for config file...")
        if not os.path.isfile(self.config_path):
            if self.config_path == "station_config.yaml":
                logger.warning(
                    f"\t{Emojis.WARNING}No config file found. Attempting configuration via environment variables...")
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
        """
        Setup and validate the runtime environment (development|production) of the station API
        Returns:

        """
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

    def _setup_station_environment(self):
        """
        After potential config files are found, parse the environment variables to override the config file values if
        they exist.
        Validate the configuration from both options.

        Returns:

        """

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

        # parse environment variables
        self._setup_station_api()
        self._setup_fernet()
        self._setup_station_auth()
        self._setup_registry_connection()
        self._setup_minio_connection()

    def _setup_station_api(self):
        """
        Configure the station api url, port and database connection from environment variables or config file.
        Returns:

        """
        # Try to find api host and port in environment variables
        env_station_host = os.getenv(StationEnvironmentVariables.STATION_API_HOST.value)
        if env_station_host:
            logger.debug(f"\t{Emojis.INFO}Overriding station api host with env var specification.")
            self.config.host = env_station_host
        env_station_port = os.getenv(StationEnvironmentVariables.STATION_API_PORT.value)
        if env_station_port:
            logger.debug(f"\t{Emojis.INFO}Overriding station api port with env var specification.")
            self.config.port = int(env_station_port)
        station_db = os.getenv(StationEnvironmentVariables.STATION_DB.value)
        if station_db:
            logger.debug(f"\t{Emojis.INFO}Overriding station db with env var specification.")
            self.config.db = station_db

        if "sqlite" in self.config.db.lower():
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   SQLite database not supported for production mode.")
            else:
                logger.warning(f"{Emojis.WARNING}   SQLite database only supported in development mode.")

    def _setup_fernet(self):
        """
        Configure the fernet key from environment variables or config file.
        In the development mode if none is given generate a new one.
        Raise an error if no key is given in production mode.
        Returns:

        """
        env_fernet_key = os.getenv(StationEnvironmentVariables.FERNET_KEY.value)

        if not env_fernet_key and not self.config.fernet_key:
            # if fernet key is given in production raise an error
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   No fernet key specified in config or env vars.")
            # generate new key in development mode
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

    def _setup_station_auth(self):
        """
        Configure the connection to the station auth from environment variables or config file.
        Optional in development mode, raises an error if not configured in production mode.
        Returns:

        """
        logger.info(f"{Emojis.INFO}Setting up station authentication...")
        # check if station auth is configured via environment variables
        env_auth_server, env_auth_port, env_auth_robot, env_auth_robot_secret = self._get_internal_service_env_vars(
            host=StationEnvironmentVariables.AUTH_SERVER_HOST,
            port=StationEnvironmentVariables.AUTH_SERVER_PORT,
            user=StationEnvironmentVariables.AUTH_ROBOT_ID,
            secret=StationEnvironmentVariables.AUTH_ROBOT_SECRET
        )

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
                robot_secret=SecretStr(env_auth_robot_secret)
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
        """
        Configure the connection to the central container registry from environment variables or config file.
        Raises an error if not configured in production mode.
        Returns:

        """
        logger.info(f"Setting up registry connection...")
        env_registry, env_registry_user, env_registry_password = self._get_external_service_env_vars(
            url=StationEnvironmentVariables.REGISTRY_URL,
            client_id=StationEnvironmentVariables.REGISTRY_USER,
            client_secret=StationEnvironmentVariables.REGISTRY_PW
        )

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

    def _setup_minio_connection(self):
        """
        Configure the connection to the minio storage from environment variables or config file.
        Raises an error if not configured in production mode.
        Returns:

        """
        logger.info(f"Setting up minio connection...")
        # get the environment variables for minio
        env_connection = self._get_internal_service_env_vars(
            host=StationEnvironmentVariables.MINIO_HOST,
            port=StationEnvironmentVariables.MINIO_PORT,
            user=StationEnvironmentVariables.MINIO_ACCESS_KEY,
            secret=StationEnvironmentVariables.MINIO_SECRET_KEY
        )
        env_minio_host, env_minio_port, env_minio_access_key, env_minio_secret_key = env_connection

        # get minio from config file or construct dummy
        _minio_config = False
        minio_config = self.config.minio
        if minio_config:
            _minio_config = True
            logger.debug("Minio config found, checking for env vars.")
        else:
            minio_config = MinioSettings.construct()

        # override minio config if config and env vars are present and validate afterwards
        if _minio_config and (env_minio_host or env_minio_port or env_minio_access_key or env_minio_secret_key):
            logger.debug(f"Overriding minio config with env var specifications.")
            if env_minio_host:
                minio_config.host = env_minio_host
            if env_minio_port:
                minio_config.port = env_minio_port
            if env_minio_access_key:
                minio_config.access_key = env_minio_access_key
            if env_minio_secret_key:
                minio_config.secret_key = env_minio_secret_key
            _minio_config = True
        # no minio config found
        elif not _minio_config and not (env_minio_host and env_minio_access_key and env_minio_secret_key):
            _minio_config = False

        # no config but environment variables are found
        elif not _minio_config and (env_minio_host and env_minio_access_key and env_minio_secret_key):
            logger.debug(f"{Emojis.INFO}No minio config found, creating new one from env vars.")
            minio_config.host = env_minio_host
            minio_config.access_key = env_minio_access_key
            minio_config.secret_key = env_minio_secret_key
            if env_minio_port:
                minio_config.port = env_minio_port
            _minio_config = True

        # log minio config and status
        if _minio_config:
            # validate the overridden config
            self.config.minio = MinioSettings(**minio_config.dict())
            logger.info(f"Minio: host - {self.config.minio.host}, port - {self.config.minio.port}")
        else:
            # raise error if no minio is configured in production mode
            if self.config.environment == StationRuntimeEnvironment.PRODUCTION:
                raise ValueError(f"{Emojis.ERROR}   No minio config specified in config or env vars")
            else:
                logger.warning(f"No minio config specified in config or env vars, ignoring in development mode")

    @staticmethod
    def _get_external_service_env_vars(url: StationEnvironmentVariables,
                                       client_id: StationEnvironmentVariables,
                                       client_secret: StationEnvironmentVariables) -> Tuple[str, str, str]:
        """
        Get the tuple of connection variables for an external service from environment variables.
        Args:
            url:
            client_id:
            client_secret:

        Returns:

        """
        env_url = os.getenv(url.value)
        env_client_id = os.getenv(client_id.value)
        env_client_secret = os.getenv(client_secret.value)
        return env_url, env_client_id, env_client_secret

    @staticmethod
    def _get_internal_service_env_vars(
            host: StationEnvironmentVariables,
            port: StationEnvironmentVariables,
            user: StationEnvironmentVariables,
            secret: StationEnvironmentVariables) -> Tuple[str, int, str, str]:
        """
        Get the tuple of connection variables for an internal service from environment variables.
        Args:
            host:
            port:
            user:
            secret:

        Returns:

        """
        env_server_host = os.getenv(host.value)
        env_server_port = os.getenv(port.value)
        if env_server_port:
            env_server_port = int(env_server_port)
        env_server_user = os.getenv(user.value)
        env_server_secret = os.getenv(secret.value)
        return env_server_host, env_server_port, env_server_user, env_server_secret


settings = Settings()
