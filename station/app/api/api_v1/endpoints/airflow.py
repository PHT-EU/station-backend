from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from station.app.api import dependencies
from station.clients.airflow.client import airflow_client
from station.app.schemas.airflow import AirflowInformation, AirflowTaskLog, AirflowRun, AirflowRunMsg
from station.app.schemas.local_trains import LocalTrainRun
from station.app.crud.crud_local_train import local_train


router = APIRouter()


@router.post("/{dag_id}/run", response_model=AirflowRun)
def run(run_msg: AirflowRunMsg, dag_id: str, db: Session = Depends(dependencies.get_db)):
    """
    Trigger a dag run and return the run_id of the run
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param run_msg: UID of the train
    @param db:  reference to the postgres database
    """
    error_msg = None
    run_id = None
    trigger_normal = None

    if dag_id == "run_local":

        try:
            config = local_train.get_train_config(db, run_msg.train_id)
            run_id = airflow_client.trigger_dag("run_local", config)
            run_information = LocalTrainRun(train_id=run_msg.train_id, run_id=run_id)
            local_train.create_run(db, obj_in=run_information)
            trigger_normal = True
        except Exception as error:
            trigger_normal = False
            error_msg = error

    elif dag_id == "run_pht_train":
        pass
        # run_id = docker_trains.run_train(db, train_id, run_config)
        # return run_id
    return {"run_id": run_id,
            "dag_id": dag_id,
            "train_id": run_msg.train_id,
            "start_date": datetime.now(),
            "trigger_normal": trigger_normal,
            "error_msg": error_msg
            }


@router.get("/run/log/{run_id}/{dag_id}", response_model=AirflowInformation)
def get_airflow_run_information(run_id: str, dag_id: str):
    """
    Get information about one airflow DAG execution.
    @param dag_id: ID of the DAG e.G. "run_local" , "run_pht_train" etc.
    @param run_id: Airflow run ID
    @return:
    """
    run_info = airflow_client.get_run_information(dag_id, run_id)
    return run_info


@router.get("/task/log/{dag_id}/{run_id}/{task_id}/{task_try_number}", response_model=AirflowTaskLog)
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
