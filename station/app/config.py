from dotenv import load_dotenv, find_dotenv

from station.app.clients import StationClients
from station.app.settings import Settings
from station.app.cache import Cache

load_dotenv(find_dotenv())

settings = Settings()
settings.setup()

clients = StationClients(settings)
clients.initialize()

cache = Cache(
    host=settings.config.redis.host,
    port=settings.config.redis.port,
    db=settings.config.redis.db,
    password=settings.config.redis.password,
)
