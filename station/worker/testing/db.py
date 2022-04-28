from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# TODO get connection from airflow

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://admin:admin@localhost/pht_station_1"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # connect_args={"check_same_thread": False}  For sqlite db
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
