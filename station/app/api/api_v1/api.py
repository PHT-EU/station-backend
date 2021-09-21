from fastapi import APIRouter
from station.app.api.api_v1.endpoints import federated_trains, datasets, protocol, docker_trains, station, station_status, local_trains

api_router = APIRouter()

# Include the routers defined in the endpoints file in the main api

api_router.include_router(station.router, tags=["Station"])
api_router.include_router(docker_trains.router, tags=["PHT 1.0"])
api_router.include_router(federated_trains.router, tags=["Federated Trains"])
api_router.include_router(datasets.router, tags=["Datasets"])
api_router.include_router(protocol.router, tags=["Protocol"])
api_router.include_router(station_status.router, tags=["Station Status"])
api_router.include_router(local_trains.router, tags=["Run Local Trains"])


