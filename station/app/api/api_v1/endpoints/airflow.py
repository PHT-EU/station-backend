from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from station.app.api import dependencies
from station.clients.airflow.client import airflow_client
from station.app.schemas.airflow import AirflowInformation, AirflowTaskLog, AirflowRun
from station.app.schemas.local_trains import LocalTrainRun
from station.app.crud.crud_local_train import local_train

router = APIRouter()


@router.post("/{train_id}/{dag_id}/run", response_model=AirflowRun)
def run(train_id: str, dag_id: str, db: Session = Depends(dependencies.get_db)):
    """
    Trigger a dag run and return the run_id of the run
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param train_id: UID of the train
    @param db:  reference to the postgres database
    """
    if dag_id == "run_local":
        config = local_train.get_train_config(db, train_id)
        run_id = airflow_client.trigger_dag("run_local", config)
        run_information = LocalTrainRun(train_id=train_id, run_id=run_id)
        local_train.create_run(db, obj_in=run_information)
    elif dag_id == "run_pht_train":
        pass
        # run_id = docker_trains.run_train(db, train_id, run_config)
        # return run_id
    return {"run_id": run_id}


@router.get("/getAirflowRun/{run_id}/{dag_id}", response_model=AirflowInformation)
def get_airflow_run_information(run_id: str, dag_id: str):
    """
    Get information about one airflow DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_run_information(dag_id, run_id)
    return run_info


@router.get("/getAirflowTaskLog/{dag_id}/{run_id}/{task_id}/{task_try_number}", response_model=AirflowTaskLog)
def get_airflow_task_log(dag_id: str, run_id: str, task_id: str, task_try_number: int):
    """
    Get log of a task in a DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param task_try_number:
    @param task_id: id of teh task
    @param run_id: Airflow run ID
    @return:
    """
    run_info_data = airflow_client.get_task_log(dag_id, run_id, task_id, task_try_number)
    return {"run_info": run_info_data}
