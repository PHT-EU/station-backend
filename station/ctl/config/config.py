from pydantic import BaseSettings

from station.ctl.config.validators import ApplicationEnvironment


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    version: str
    host: str
