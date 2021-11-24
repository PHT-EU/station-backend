from fastapi import APIRouter
from station.clients.airflow.client import airflow_client

router = APIRouter()

@router.get("/airflow/getAirflowRun/{run_id}/{dag_id}")
def get_airflow_run_information(run_id: str, dag_id: str):
    """
    Get information about one airflow DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_run_information(dag_id, run_id)
    return run_info
