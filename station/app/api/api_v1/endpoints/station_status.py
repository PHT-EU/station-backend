from fastapi import APIRouter, Depends
from station.clients.airflow.client import airflow_client
from station.clients.harbor_client import harbor_client
from station.clients.minio.client import minio_client
from station.clients.fhir.client import FhirClient
from station.app.api import dependencies
from sqlalchemy.orm import Session
from station.app.crud import datasets
import psutil

router = APIRouter()
"""
The station status  endpoint returns the status of local and global components  (fhir  airflow harbo minio
"""


@router.get("/status/Airflow")
def status_airflow():
    status = airflow_client.health_check()
    return status


@router.get("/status/Harbor")
def harbor_status():
    status = harbor_client.health_check()
    return status


@router.get("/status/Minio")
def status_minio():
    status = minio_client.health_check()
    # TODO add externall added MinIO to the health check
    return status


@router.get("/status/fhir")
def status_Fhir(db: Session = Depends(dependencies.get_db)):
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


@router.get("/status/total_memory_util")
def status_total_memory_util():
    return psutil.virtual_memory().percent


@router.get("/status/total_cpu_util")
def status_total_cpu_util():
    return psutil.cpu_percent(interval=1, percpu=True)


@router.get("/status/total_gpu_util")
def status_total_gpu_util():
    pass
    #TODO get the GPU recorces

@router.get("/status/total_disk_util")
def status_total_disk_util():
    pass
