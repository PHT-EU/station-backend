import os

import uvicorn
from dotenv import load_dotenv, find_dotenv
from station.app.db.setup_db import setup_db, reset_db
from station.app.config import settings
from station.app.config import StationRuntimeEnvironment
from station.app import cache
from station.clients.minio import MinioClient
from station.clients import harbor_client


def setup():
    load_dotenv(find_dotenv())
    settings.setup()
    setup_db(dev=False, reset=False)
    # minio
    minio_client = MinioClient()
    minio_client.setup_buckets()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    setup()
    harbor_client.harbor_client = harbor_client.HarborClient(
        api_url=settings.config.registry.api_url,
        username=settings.config.registry.user,
        password=settings.config.registry.password,
    )

    cache.redis_cache = cache.Cache(settings.config.redis.host)

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

