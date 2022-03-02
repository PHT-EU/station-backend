from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv, find_dotenv
from airflow.providers.postgres.hooks.postgres import PostgresHook

load_dotenv(find_dotenv())

# SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

if os.getenv("STATION_DB"):
    SQLALCHEMY_DATABASE_URL = os.getenv('STATION_DB')
else:
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://admin:admin@localhost/pht_station"


print("SQL DB URL : {}".format(SQLALCHEMY_DATABASE_URL))
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # connect_args={"check_same_thread": False}  For sqlite db
)

#hook = PostgresHook(postgres_conn_id=os.getenv('STATION_DB_CONN_ID'))
#engine = hook.get_sqlalchemy_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("SessionLocal got created")
