from fastapi import APIRouter

from station.clients.airflow.client import airflow_client
from station.clients.harbor_client import harbor_client
from station.clients.minio.client import MinioClient
from station.app.schemas import station_status as status_schema
from loguru import logger

from station.app.config import clients

import psutil

# todo singleton minio client
# TODO resolve connection error to MinIO
#minio_client = MinioClient()
router = APIRouter()
"""
The station status  endpoint returns the status of local and global components  (fhir  airflow harbo minio
"""


def service_health_check():
    """
    Get the health status of all connected services
    """
    service_status = []
    services = {
        "airflow": airflow_client.health_check(),
        "harbor": harbor_client.health_check(),
#        "minio": minio_client.health_check(),
    }
    for service, health in services.items():
        service_status.append(status_schema.ServiceStatus(
            name=service,
            status=health
        ))
    return service_status

def get_hardware_resources_status():
    # get memory statistics
    memory_stats = psutil.virtual_memory()
    memory_usage = status_schema.MemoryUsage(
        total=memory_stats.total,
        available=memory_stats.available,
        percent=memory_stats.percent,
        used=memory_stats.used,
        free=memory_stats.free
    )

    # get disk statistics
    disk_util = psutil.disk_usage('./')
    disk_usage = status_schema.DiskUsage(
        total=disk_util.total,
        used=disk_util.used,
        free=disk_util.free,
        percent=disk_util.percent
    )

    # cpu usage per core
    cpu_usage = psutil.cpu_percent(interval=None, percpu=True)

    # todo GPU
    return status_schema.HardwareResources(
        memory=memory_usage,
        cpu=cpu_usage,
        disk=disk_usage,
    )


@router.get("", response_model=status_schema.StationStatus)
async def get_station_status():
    hardware = get_hardware_resources_status()
    services = service_health_check()

    return status_schema.StationStatus(
        hardware=hardware,
        services=services
    )

# @router.get("/container_resource_util")
# def status_docker_container_resource_use():
#     """
#     get information for all docker containers
#     """
#     return dockerClient.get_stats_all()
#
#
# @router.get("/container/{container_id}")
# def status_docker_container_resource_use(container_id: Any):
#     """
#     get information for container id
#     """
#     return dockerClient.get_stats_container(container_id)
#
#
# @router.get("/container_info")
# def container_info():
#     return dockerClient.get_information_all()
