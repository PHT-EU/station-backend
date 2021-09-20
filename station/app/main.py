from fastapi import FastAPI

from station.app.api.api_v1.api import api_router
from dotenv import load_dotenv, find_dotenv
from fastapi.middleware.cors import CORSMiddleware
import logging

load_dotenv(find_dotenv())
app = FastAPI(
    title="PHT Station"
)

# TODO remove full wildcard for production
origins = [
    "http://localhost:8080",
    "http://localhost:8080/",
    "http://localhost:8081",
    # "http://localhost:3000",
    # "http://localhost",
    # "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
