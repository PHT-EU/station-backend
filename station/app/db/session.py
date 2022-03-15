from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

if os.getenv("STATION_DB"):
    SQLALCHEMY_DATABASE_URL = os.getenv('STATION_DB')
else:
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://admin:admin@localhost/pht_station"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # connect_args={"check_same_thread": False}  For sqlite db
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

