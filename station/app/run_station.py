import os

import uvicorn
from dotenv import load_dotenv, find_dotenv
from station.app.db.setup_db import setup_db, reset_db
from station.app.config import settings, Settings
from station.app.config import StationRuntimeEnvironment
from station.app.cache import redis_cache, Cache
from station.clients.minio import MinioClient


def setup():
    load_dotenv(find_dotenv())
    settings.setup()
    setup_db(dev=os.getenv("ENVIRONMENT") != "production")

    # minio
    minio_client = MinioClient()
    minio_client.setup_buckets()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    setup()

    print(settings.config)

    # Configure logging behaviour
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    uvicorn.run(
        "station.app.main:app",
        port=settings.config.port,
        host=settings.config.host,
        reload=settings.config.environment == StationRuntimeEnvironment.DEVELOPMENT,
        log_config=log_config
    )
