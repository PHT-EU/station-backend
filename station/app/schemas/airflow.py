from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskInstances(BaseModel):
    dag_id: str
    duration: Optional[float]
    end_date: Optional[datetime]
    execution_date: datetime
    executor_config: str
    hostname: str
    max_tries: int
    operator: str
    pid: Optional[int]
    priority_weight: int
    queue: str
    queued_when: Optional[datetime]
    start_date: Optional[datetime]
    state: Optional[str]
    task_id: str
    try_number: int
    unixname: str


class Tasklist(BaseModel):
    task_instances: List[TaskInstances]
    total_entries: int


class AirflowInformation(BaseModel):
    conf: dict
    dag_id: str
    dag_run_id: str
    end_date: Optional[datetime]
    execution_date: datetime
    external_trigger: bool
    logical_date: datetime
    start_date: Optional[datetime]
    state: str
    tasklist: Tasklist


class AirflowTaskLog(BaseModel):
    run_info: str


class AirflowRunMsg(BaseModel):
    train_id: str


class AirflowRun(BaseModel):
    run_id: str
    dag_id: str
    train_id: str
    start_date: datetime

