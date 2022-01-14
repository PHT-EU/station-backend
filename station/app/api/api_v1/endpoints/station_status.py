from typing import Any

from fastapi import APIRouter, Depends
from station.clients.airflow.client import airflow_client
from station.clients.harbor_client import harbor_client
from station.clients.minio.client import MinioClient
from station.clients.fhir.client import FhirClient
from station.clients.docker.client import dockerClient
from station.app.api import dependencies
from sqlalchemy.orm import Session
from station.app.crud import datasets
import psutil

minio_client = MinioClient()
router = APIRouter()
"""
The station status  endpoint returns the status of local and global components  (fhir  airflow harbo minio
"""
#TODO Response models

@router.get("/Airflow")
def status_airflow():
    """
    Get the health status of the connected Airflow instance
    """
    status = airflow_client.health_check()
    return status


@router.get("/Harbor")
def harbor_status():
    """
    Get the health status of the central harbor instance
    """
    status = harbor_client.health_check()
    return status


@router.get("/Minio")
def status_minio():
    """
    Get the health status of the minio instance
    """
    status = minio_client.health_check()
    # TODO add external added MinIO to the health check
    return status


@router.get("/fhir")
def status_Fhir(db: Session = Depends(dependencies.get_db)):
    """
    Get the health status of all concectetd fhir servers
    """
    all_datasets = datasets.get_multi(db=db, limit=None)
    statuses = []
    # Iterate over all addet data sorces
    for dataset in all_datasets:
        # select only the fhir servers
        if dataset.storage_type == "fhir":
            # health check on the server
            fhir_client = FhirClient(dataset.access_path, dataset.fhir_user, dataset.fhir_password,
                                     server_type=dataset.fhir_server_type)
            status = fhir_client.health_check()
            status["name"] = dataset.name
            statuses.append(status)
    fhir_client = FhirClient()
    status = fhir_client.health_check()
    status["name"] = "main"
    statuses.append(status)
    return statuses


@router.get("/total_memory_util")
def status_total_memory_util():
    """
    get the current memory util of the system
    """
    memory_stats = psutil.virtual_memory()
    response = {
        "total": memory_stats.total,
        "available": memory_stats.available,
        "percent": memory_stats.percent,
        "used": memory_stats.used,
        "free": memory_stats.free,
        # "active": memory_stats.active,
        # "inactive": memory_stats.inactive,
        # "buffers": memory_stats.buffers,
        # "cached": memory_stats.cached,
        # "shared": memory_stats.shared,
        # "slab": memory_stats.slab,
    }
    return response


@router.get("/total_cpu_util")
def status_total_cpu_util():
    """
    get the current cpu utilisation of the cpu
    """
    return psutil.cpu_percent(interval=1, percpu=True)


@router.get("/total_gpu_util")
def status_total_gpu_util():
    """
    get the current gpu utilisation of connected GPUs
    """
    pass
    # TODO get the GPU recorces


@router.get("/total_disk_util")
def status_total_disk_util():
    """
        get the current gpu utilisation of connected GPUs
    """
    disk_util = psutil.disk_usage('./')
    disk_util_dict = {"total": disk_util.total,
                      "used": disk_util.used,
                      "free": disk_util.free,
                      "percent": disk_util.percent}
    return disk_util_dict


@router.get("/container_resource_util")
def status_docker_container_resource_use():
    """
    get information for all docker containers
    """
    return dockerClient.get_stats_all()


@router.get("/container/{container_id}")
def status_docker_container_resource_use(container_id: Any):
    """
    get information for container id
    """
    return dockerClient.get_stats_container(container_id)


@router.get("/container_info")
def container_info():
    return dockerClient.get_information_all()
