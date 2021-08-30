from fastapi import APIRouter, Depends
from station.clients.airflow.client import airflow_client
from station.clients.harbor_client import harbor_client
from station.clients.minio.client import minio_client
from station.clients.fhir.client import FhirClient
from station.app.api import dependencies
from sqlalchemy.orm import Session
from station.app.crud import datasets

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
    #TODO add externall added MinIO to the health check
    return status


@router.get("/status/fhir")
def status_Fhir(db: Session = Depends(dependencies.get_db)):
    all_datasets = datasets.get_multi(db=db, limit=None)

    for dataset in all_datasets:
        print(dataset.name)
        if dataset.storage_type == "fhir":
            fhir_client = FhirClient(dataset.aaccess_path,dataset.fhir_user, dataset.fhir_password, server_type= dataset.fhir_server_type)
            status = fhir_client.health_check()

            print(status)
    fhir_client = FhirClient()
    status = fhir_client.health_check()
    return status
