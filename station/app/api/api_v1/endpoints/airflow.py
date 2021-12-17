from fastapi import APIRouter
from station.clients.airflow.client import airflow_client

router = APIRouter()

# TODO Add pydantic schema
@router.get("/getAirflowRun/{run_id}/{dag_id}")
def get_airflow_run_information(run_id: str, dag_id: str):
    """
    Get information about one airflow DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_run_information(dag_id, run_id)
    return run_info

# TODO Add pydantic schema
@router.get("/getAirflowTaskLog/{dag_id}/{run_id}/{task_id}/{task_try_number}")
def get_airflow_task_log(dag_id: str, run_id: str, task_id: str, task_try_number: int):
    """
    Get log of a task in a DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param task_try_number:
    @param task_id: id of teh task
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_task_log(dag_id, run_id, task_id, task_try_number)
    return run_info
