from authup.plugins.asgi import AuthupASGIMiddleware
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from station.app.api.api_v1.api import api_router
from station.app.auth import authorized_user
from station.app.config import settings

load_dotenv(find_dotenv())

settings.setup()


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


print(settings.config.auth.auth_url)

app.add_middleware(
    AuthupASGIMiddleware,
    authup_url=settings.config.auth.auth_url,
)

app.include_router(
    api_router,
    prefix="/api",
    # dependencies=[Depends(authorized_user)],
)
