
from sqlalchemy.orm import sessionmaker

from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.settings import Session
from station.app.db.session import *
from station.app.db.setup_db import *


def create_session(connection_id: str) -> Session:
    """
    Creates Session from connection_id string
    """

    hook = PostgresHook(postgres_conn_id=connection_id)
    engine = hook.get_sqlalchemy_engine()

    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session()

    return session

