from fastapi import APIRouter, Body, Depends
from station.clients.airflow.client import airflow_client
from station.clients.harbor_client import harbor_client
from station.clients.minio.client import minio_client
from station.clients.fhir.client import FhirClient
router = APIRouter()


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
    #TODO add externall addet MinIO to the health check
    return status


@router.get("/status/fhir")
def status_Fhir():
    fhir_client = FhirClient()
    fhir_client.health_check()

