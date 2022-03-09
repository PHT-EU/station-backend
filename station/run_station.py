import os

import uvicorn
from dotenv import load_dotenv, find_dotenv
from station.app.db.setup_db import setup_db, reset_db
from app.config import settings
from app.config import StationRuntimeEnvironment

if __name__ == '__main__':
    load_dotenv(find_dotenv())
    # todo remove reset in production
    # reset_db(dev=os.getenv("ENVIRONMENT") != "prod")
    setup_db(dev=os.getenv("ENVIRONMENT") != "prod")

    # Configure logging behaviour
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    # initialize settings
    station_config = settings.setup()
    print(settings.config)

    uvicorn.run("app.main:app",
                port=station_config.port,
                host=station_config.host,
                reload=station_config.environment == StationRuntimeEnvironment.DEVELOPMENT,
                log_config=log_config
                )
