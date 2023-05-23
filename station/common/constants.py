from enum import Enum

CERTS_REGEX = r"https\.certs\[([0-9]*)\]"


class ApplicationEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class DockerVolumes(Enum):
    POSTGRES = "pg_pht_station"


class DockerNetworks(Enum):
    STATION = "pht-station"


class PHTImages(Enum):
    API = "ghcr.io/pht-medic/station-api"
    UI = "ghcr.io/pht-medic/station-ui"
    AUTH = "ghcr.io/authup/authup"
    AIRFLOW = "ghcr.io/pht-medic/airflow"


class ServiceImages(Enum):
    MINIO = "minio/minio:RELEASE.2022-11-11T03-44-20Z"
    POSTGRES = "postgres:14"
    REDIS = "redislabs/rejson:latest"
    TRAEFIK = "traefik:v2.8"
    BLAZE = "samply/blaze:latest"


class DefaultValues(Enum):
    """
    Default values for the station configuration
    """

    FERNET_KEY = "your_fernet_key"
    ADMIN = "admin"
    ADMIN_PASSWORD = "password"
    PRIVATE_KEY = "/path/to/private_key.pem"
    STATION_DOMAIN = "example-station.com"
    CERT = "example-cert.pem"
    KEY = "example-key.pem"
    DOMAIN = "station.localhost"
    ROBOT_ID = "central-robot-id"
    ROBOT_SECRET = "central-robot-secret"
    HTTP_PORT = 80
    HTTPS_PORT = 443


class PHTDirectories(Enum):
    SERVICE_DATA_DIR = "service_data"
    SERVICE_LOG_DIR = "logs"
    CONFIG_DIR = "configs"
    CERTS_DIR = "certs"
    STATION_DATA_DIR = "station_data"
    SETUP_SCRIPT_DIR = "setup_scripts"


class DataDirectories(str, Enum):
    MODELS = "models"
    TRAINS = "trains"
    DATASETS = "datasets"
    LOCAL_TRAINS = "localtrains"


class ServiceNames(Enum):
    AUTH = "auth"
    POSTGRES = "postgres"
    REDIS = "redis"
    MINIO = "minio"


class Icons(Enum):
    CHECKMARK = "✓"
    CROSS = "❌"
    WARNING = "⚠"
