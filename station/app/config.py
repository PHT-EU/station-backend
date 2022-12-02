from dotenv import load_dotenv, find_dotenv

from station.app.clients import StationClients
from station.app.settings import Settings
from station.app.cache import Cache

load_dotenv(find_dotenv())

settings = Settings()
# settings.setup()

clients = StationClients(settings)
# clients.initialize()

cache = None
