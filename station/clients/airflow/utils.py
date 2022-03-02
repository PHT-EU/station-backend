import logging
import os
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy.orm import sessionmaker
from station.app.db.setup_db import *
from station.app.db.session import *


class UtilityFunctions:
    def __init__(self):
         self.connection_id = 'psql_station_db'

    def create_session(self):

        hook = PostgresHook(postgres_conn_id=self.connection_id)
        engine = hook.get_sqlalchemy_engine()
        print("Engine : {}".format(engine))

        session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        #setup_db()
        print("Setup db executed")



        return session



utils = UtilityFunctions()
utils.create_session()