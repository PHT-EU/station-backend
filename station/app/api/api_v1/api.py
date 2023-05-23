from fastapi import APIRouter

from station.app.api.api_v1.endpoints import (
    airflow,
    datasets,
    docker_trains,
    fhir,
    local_trains,
    master_images,
    notifications,
    station,
    station_status,
)

api_router = APIRouter()

# Include the routers defined in the endpoints file in the main api

api_router.include_router(station.router, prefix="/station", tags=["Station"])
api_router.include_router(
    docker_trains.router, prefix="/trains/docker", tags=["Trains", "PHT 1.0"]
)
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(
    station_status.router, prefix="/station/status", tags=["Station"]
)
api_router.include_router(
    local_trains.router, prefix="/local-trains", tags=["Local Trains"]
)
api_router.include_router(airflow.router, prefix="/airflow", tags=["Airflow"])
api_router.include_router(fhir.router, prefix="/fhir/server", tags=["FHIR"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)
api_router.include_router(
    master_images.router, prefix="/master-images", tags=["Master Images"]
)
