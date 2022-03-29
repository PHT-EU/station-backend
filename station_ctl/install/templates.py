from typing import List, Tuple

from jinja2 import Environment, PackageLoader


def render_station_config():
    pass


def render_airflow_config(domain: str, sql_alchemy_conn: str, env: Environment = None) -> str:
    if not env:
        env = _get_template_env()

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
        env = _get_template_env()

    # render traefik config
    traefik_config = _make_traefik_config(
        env=env,
        http_port=http_port,
        https_port=https_port,
        https_enabled=https_enabled,
        dashboard=True
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
        env = _get_template_env()
    template = env.get_template('init.sql.tmpl')
    return template.render(db_user=db_user)


def _make_traefik_config(
        env: Environment,
        http_port: int = 80,
        https_port: int = None,
        https_enabled: bool = True,
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
        https_enabled=https_enabled
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


def _get_template_env():
    return Environment(loader=PackageLoader('station_ctl', 'templates'))
