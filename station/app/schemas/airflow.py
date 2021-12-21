from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class TaskInstances(BaseModel):
    dag_id: str
    duration: float
    end_date: datetime
    execution_date: datetime
    executor_config: str
    hostname: str
    max_tries: int
    operator: str
    pid: int
    pool: str
    pool_slots: int
    priority_weight: int
    queue: str
    queued_when: datetime
    sla_miss: Optional[dict]
    start_date: datetime
    state: str
    task_id: str
    try_number: int
    unixname: str

class Tasklist(BaseModel):
    task_instances: list[TaskInstances]
    total_entries: int

class AirflowInformation(BaseModel):
    conf: dict
    dag_id: str
    dag_run_id: str
    end_date: datetime
    execution_date: datetime
    external_trigger: bool
    logical_date: datetime
    start_date: datetime
    state: str
    tasklist: Tasklist


class AirflowTaskLog(BaseModel):
    run_info: str
