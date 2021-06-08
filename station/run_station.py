import os

import uvicorn
from dotenv import load_dotenv, find_dotenv
from app.db.setup_db import setup_db, reset_db

if __name__ == '__main__':
    load_dotenv(find_dotenv())
    setup_db()
    # reset_db()
    uvicorn.run("app.main:app", port=8001, host="0.0.0.0", reload=True)
