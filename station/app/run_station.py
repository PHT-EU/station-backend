import uvicorn
from dotenv import load_dotenv, find_dotenv

from station.app.cache import Cache
from station.app.db.setup_db import setup_db, reset_db
from station.app.settings import StationRuntimeEnvironment
from station.app.config import settings, clients, cache


def setup():
    load_dotenv(find_dotenv())
    # settings.setup()

    # minio
    # minio_client = MinioClient()
    # minio_client.setup_buckets()


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    # setup()
    settings.setup()

    setup_db(dev=False, reset=False)
    clients.initialize()
    # cache.redis_cache = cache.Cache(settings.config.redis.host)
    cache = Cache(
        host=settings.config.redis.host,
        port=settings.config.redis.port,
        db=settings.config.redis.db,
        password=settings.config.redis.password,
    )
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

