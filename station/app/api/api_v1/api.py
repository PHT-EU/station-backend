from fastapi import APIRouter
from station.app.api.api_v1.endpoints import datasets, protocol, docker_trains, station, \
    station_status, local_trains, airflow, fhir

api_router = APIRouter()

# Include the routers defined in the endpoints file in the main api

api_router.include_router(station.router, tags=["Station"])
api_router.include_router(docker_trains.router, prefix="/trains/docker", tags=["PHT 1.0"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(protocol.router, tags=["Protocol"])
api_router.include_router(station_status.router, tags=["Station Status"])
api_router.include_router(local_trains.router, prefix="/localTrains", tags=["Run Local Trains"])
api_router.include_router(airflow.router, prefix="/airflow", tags=["Airflow"])
api_router.include_router(fhir.router, prefix="/fhir", tags=["FHIR"])
