from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
# TODO store db credentials in environment variables
if os.getenv("STATION_DB"):
    SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://admin:admin@postgres/{os.getenv('STATION_DB')}"
else:
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://admin:admin@localhost/pht_station_1"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,  # connect_args={"check_same_thread": False}  For sqlite db
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
