import os
from typing import List, Tuple

from jinja2 import Environment

from station.ctl.util import get_template_env
from station.ctl.constants import PHTImages, ServiceImages, PHTDirectories
from station.app.config import StationEnvironmentVariables


def render_compose(config: dict, env: Environment = None) -> str:
    """
    Render the docker-compose.yml file for the given config.

    Args:
        config: config dict
        env: template Environment

    Returns:

    """
    if not env:
        env = get_template_env()
    template = env.get_template('docker-compose.yml.tmpl')

    service_images = {
        "db": ServiceImages.POSTGRES.value,
        "traefik": ServiceImages.TRAEFIK.value,
        "redis": ServiceImages.REDIS.value,
        "minio": ServiceImages.MINIO.value,
    }

    pht_images = {
        "airflow": PHTImages.AIRFLOW.value,
        "api": PHTImages.API.value,
        "ui": PHTImages.UI.value,
        "auth": PHTImages.AUTH.value,

    }

    service_data_dir = os.path.join(config["install_dir"], PHTDirectories.SERVICE_DATA_DIR.value)

    db_config = {
        "init_sql_path": config["init_sql_path"],
        "env": {
            "POSTGRES_USER": config["db"]["admin_user"],
            "POSTGRES_PASSWORD": config["db"]["admin_password"],
        }
    }

    certs_dir = str(os.path.join(config["install_dir"], PHTDirectories.CERTS_DIR.value))

    proxy_config = {
        "http_port": config["http"]["port"],
        "https_port": config["https"]["port"],
        "labels": [
            "traefik.enable=true",
            "traefik.http.routers.traefik=true"
        ],
        "traefik_config": config["traefik_config_path"],
        "router_config": config["router_config_path"],
        "certs_dir": certs_dir,
    }

    auth_config = {
        "env": {
            "ADMIN_USER": config["auth"]["admin_user"],
            "ADMIN_PASSWORD": config["auth"]["admin_password"],
        },
        "labels": [
            "traefik.enable=true",
        ]
    }

    db_connection_string = f"postgresql+psycopg2://{config['db']['admin_user']}:{config['db']['admin_password']}" \
                           f"@postgres/pht_station"
    registry_user = config["registry"]["user"]
    if "$" in registry_user:
        registry_user = registry_user.replace("$", "$$")

    api_config = {
        "env": {
            "STATION_ID": config["station_id"],
            StationEnvironmentVariables.STATION_DB.value: db_connection_string,
            StationEnvironmentVariables.FERNET_KEY.value: config["api"]["fernet_key"],
            StationEnvironmentVariables.ENVIRONMENT.value: config["environment"],
            StationEnvironmentVariables.AIRFLOW_API_URL.value: f"http://airflow:8080/api/v1/",
            StationEnvironmentVariables.AIRFLOW_USER.value: config["airflow"]["admin_user"],
            StationEnvironmentVariables.AIRFLOW_PW.value: config["airflow"]["admin_password"],
            StationEnvironmentVariables.MINIO_HOST.value: "minio",
            StationEnvironmentVariables.MINIO_PORT.value: "9000",
            StationEnvironmentVariables.MINIO_ACCESS_KEY.value: config["minio"]["admin_user"],
            StationEnvironmentVariables.MINIO_SECRET_KEY.value: config["minio"]["admin_password"],
            StationEnvironmentVariables.REDIS_HOST.value: "redis",
            StationEnvironmentVariables.AUTH_SERVER_HOST.value: "station-auth",
            StationEnvironmentVariables.AUTH_SERVER_PORT.value: 3010,
            StationEnvironmentVariables.AUTH_ROBOT_ID.value: config["auth"]["robot_id"],
            StationEnvironmentVariables.AUTH_ROBOT_SECRET.value: config["auth"]["robot_secret"],
            StationEnvironmentVariables.REGISTRY_URL.value: config["registry"]["address"],
            StationEnvironmentVariables.REGISTRY_USER.value: registry_user,
            StationEnvironmentVariables.REGISTRY_PW.value: config["registry"]["password"],

        },
        "labels": [
            "traefik.enable=true",
            "traefik.http.routers.api.tls=true",
            f'traefik.http.routers.api.rule=Host("{config["https"]["domain"]}") && PathPrefix("/api")',
            "traefik.http.services.api.loadbalancer.server.port=8000"
        ]
    }

    minio_config = {
        "env": {
            "MINIO_ROOT_USER": config["minio"]["admin_user"],
            "MINIO_ROOT_PASSWORD": config["minio"]["admin_password"],
        },
        "labels": [
            "traefik.enable=true",
            "traefik.http.routers.minio.tls=true",
            f'traefik.http.routers.minio.rule=Host("minio.{config["https"]["domain"]}")',
            "traefik.http.routers.minio.service=minio",
            "traefik.http.services.minio.loadbalancer.server.port=9000",
            "traefik.http.routers.minio-console.tls=true",
            f'traefik.http.routers.minio-console.rule=Host("minio-console.{config["https"]["domain"]}")',
            "traefik.http.routers.minio-console.service=minio-console",
            "traefik.http.services.minio-console.loadbalancer.server.port=9001"
        ]
    }
    airflow_config = {
        "private_key": config["central"]["private_key"],
        "config_path": config["airflow_config_path"],
        "env": {
            "STATION_ID": config["station_id"],
            "AIRFLOW_USER": config["airflow"]["admin_user"],
            "AIRFLOW_PW": config["airflow"]["admin_password"],
            "HARBOR_URL": config["registry"]["address"],
            "HARBOR_USER": registry_user,
            "HARBOR_PW": config["registry"]["password"],

        },
        "labels": [
            "traefik.enable=true",
            "traefik.http.routers.airflow.tls=true",
            f'traefik.http.routers.airflow.rule=Host("{config["https"]["domain"]}") && PathPrefix("/airflow")',
            "traefik.http.services.airflow.loadbalancer.server.port=8080"
        ]
    }

    return template.render(
        service_images=service_images,
        pht_images=pht_images,
        version=config['version'],
        service_data_dir=service_data_dir,
        db_config=db_config,
        proxy_config=proxy_config,
        auth_config=auth_config,
        api_config=api_config,
        minio_config=minio_config,
        airflow_config=airflow_config
    )


def render_airflow_config(domain: str, sql_alchemy_conn: str, env: Environment = None) -> str:
    if not env:
        env = get_template_env()

    template = env.get_template('airflow.cfg.tmpl')
    return template.render(domain=domain, sql_alchemy_conn=sql_alchemy_conn)


def render_traefik_configs(
        http_port: int = 80,
        https_port: int = 443,
        https_enabled: bool = True,
        domain: str = None,
        certs: List[dict] = None,
        env: Environment = None) -> Tuple[str, str]:
    """
    Render static config files for the traefik proxy.

    Args:
        http_port: which port to use for http traffic
        https_port: which port to use for https traffic
        https_enabled: boolean whether to enable https traffic
        domain: domain to use for https traffic
        certs: certificates for the given domain
        env: template Environment

    Returns: Tuple of the traefik config and router config yaml files as strings

    """

    # initialize environment if it is not given
    if not env:
        env = get_template_env()

    # render traefik config
    traefik_config = _make_traefik_config(
        env=env,
        http_port=http_port,
        https_port=https_port,
        https_enabled=https_enabled,
        dashboard=True,
        domain=domain,
    )

    # render traefik router config
    router_config = _make_traefik_router_config(
        env=env,
        https_enabled=https_enabled,
        domain=domain,
        certs=certs
    )

    return traefik_config, router_config


def render_init_sql(db_user: str, env: Environment = None) -> str:
    """
    Render the init.sql file for setting up the postgres database.
    The given user and two databases will be created with this script, the user is given full permissions on all
    created databases.

    Args:
        db_user: username for the DBMS
        env: template Environment

    Returns:

    """
    if not env:
        env = get_template_env()
    template = env.get_template('init.sql.tmpl')
    return template.render(db_user=db_user)


def _make_traefik_config(
        env: Environment,
        http_port: int = 80,
        https_port: int = None,
        https_enabled: bool = True,
        domain: str = None,
        dashboard: bool = False) -> str:
    """
    Render the general traefik config file.

    Args:
        env: template Environment
        http_port: port to use for http traffic
        https_port: port to use for https traffic
        https_enabled: https enabled
        dashboard: whether to enable the traefik dashboard

    Returns: string containing the content of the traefik config yaml file

    """
    template = env.get_template('traefik/traefik.yml.tmpl')
    return template.render(
        dashboard=dashboard,
        http_port=http_port,
        https_port=https_port,
        https_enabled=https_enabled,
        domain=domain
    )


def _make_traefik_router_config(
        env: Environment,
        https_enabled: bool = True,
        domain: str = None,
        certs: List[dict] = None) -> str:
    """
    Render the traefik router config file. This file contains static router configuration for the traefik proxy.
    As well the specifications on which domains and respective certificates to use for https traffic.
    Args:
        env: template Environment
        https_enabled: whether to enable https traffic
        domain: domain to use for https traffic
        certs: certificates for the given domain

    Returns: string containing the content of the traefik router config yaml file

    """
    template = env.get_template('traefik/config.yml.tmpl')
    return template.render(
        domain=domain,
        https_enabled=https_enabled,
        certs=certs
    )
