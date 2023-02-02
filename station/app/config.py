from dotenv import find_dotenv, load_dotenv

from station.app.clients import StationClients
from station.app.settings import Settings

load_dotenv(find_dotenv())

settings = Settings()
# settings.setup()

clients = StationClients(settings)
# clients.initialize()

cache = None
