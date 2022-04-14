from pydantic import BaseSettings

from station_ctl.config.validators import ApplicationEnvironment


class StationConfig(BaseSettings):
    station_id: str
    environment: ApplicationEnvironment
    version: str
    host: str
