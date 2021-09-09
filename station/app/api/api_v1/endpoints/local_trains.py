from fastapi import APIRouter, Depends
from station.clients.airflow.client import airflow_client

router = APIRouter()


@router.post("/local/trains/{local_train_id}/run")
def run_docker_train(local_train_id: str):
    print(local_train_id)
    airflow_client.trigger_dag("run_local")
