from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv
from fastapi.middleware.cors import CORSMiddleware

from station.app.api.api_v1.api import api_router
from station.app.logger import init_logging


load_dotenv(find_dotenv())


app = FastAPI(
    title="PHT Station", docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/v1/openapi.json"
)

# Setup logging
# init_logging()
# TODO remove full wildcard for production
origins = [
    "http://localhost:8080",
    "http://localhost:8080/",
    "http://localhost:8081",
    # "http://localhost:3000",
    # "http://localhost",
    "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
