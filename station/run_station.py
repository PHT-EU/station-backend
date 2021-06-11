import os

import uvicorn
from dotenv import load_dotenv, find_dotenv
from app.db.setup_db import setup_db, reset_db

if __name__ == '__main__':
    load_dotenv(find_dotenv())

    reset_db()
    setup_db()

    # Configure logging behaviour
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"

    uvicorn.run("app.main:app", port=8001, host="0.0.0.0", reload=True, log_config=log_config)
