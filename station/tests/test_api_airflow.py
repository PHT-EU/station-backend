import pytest
import os
from fastapi.testclient import TestClient

from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture()
def train_id():
    return "airflow_test"


def test_run(train_id):
    if os.getenv("ENVIRONMENT") == "testing":
        response = client.post("/api/trains/docker",
                               json={"train_id": train_id,
                                     "config": {"name": "testconfig",
                                                "airflow_config": {
                                                    "repository": f"dev-harbor.grafm.de/station_1/{train_id}",
                                                    "tag": "latest"
                                                }}})
        if response.status_code == 200:

            run_pht_train = client.post("/api/airflow/run_pht_train/run",
                                        json={"train_id": train_id})
            response_pht_train = run_pht_train.json()

            assert run_pht_train.status_code == 200
            assert response_pht_train["dag_id"] == "run_pht_train"
            assert response_pht_train["train_id"] == "airflow_test"
            assert response_pht_train["start_date"]

            execution = client.get(f"/api/trains/docker/{train_id}/executions")
            assert execution.json()[-1]["airflow_dag_run"] == response_pht_train["run_id"]

        # TODO tests for local trains


def test_run_fails(train_id):
    if os.getenv("ENVIRONMENT") == "testing":
        run_wrong_dag = client.post("/api/airflow/dag_not_there/run",
                                    json={"train_id": train_id})
        assert run_wrong_dag.status_code == 404, run_wrong_dag.text


def test_get_airflow_run_information(train_id):
    if os.getenv("ENVIRONMENT") == "testing":
        response = client.get(f"/api/trains/docker/{train_id}/executions")
        executions = response.json()
        assert len(executions) > 0
        run_id = executions[-1]["airflow_dag_run"]

        run_info_response = client.get(f"/api/airflow/logs/run_pht_train/{run_id}")
        print(run_info_response.json())
        assert run_info_response.status_code == 200

        # TODO tests for local trains


def test_get_airflow_run_information_fails():
    if os.getenv("ENVIRONMENT") == "testing":
        with pytest.raises(Exception):
            run_id_fail = client.get(f"/api/airflow/logs/run_pht_train/no_run_id")
            assert run_id_fail.status_code == 404

        with pytest.raises(Exception):
            dag_id_fail = client.get(f"/api/airflow/logs/dag_not_there/no_run_id")
            assert dag_id_fail.status_code == 404


def test_get_airflow_task_log(train_id):
    if os.getenv("ENVIRONMENT") == "testing":
        response = client.get(f"/api/trains/docker/{train_id}/executions")
        executions = response.json()
        assert len(executions) > 0
        run_id = executions[-1]["airflow_dag_run"]

        run_info_response = client.get(f"/api/airflow/logs/run_pht_train/{run_id}")
        tasklist = run_info_response.json()["tasklist"]
        for task in tasklist["task_instances"]:
            task_id = task["task_id"]
            task_info = client.get(f"/api/airflow/logs/run_pht_train/{run_id}/{task_id}")
            assert task_info.status_code == 200


def test_get_airflow_task_log_fails(train_id):
    if os.getenv("ENVIRONMENT") == "testing":
        response = client.get(f"/api/trains/docker/{train_id}/executions")
        executions = response.json()
        assert len(executions) > 0
        run_id = executions[-1]["airflow_dag_run"]

        task_info = client.get(f"/api/airflow/logs/run_pht_train/{run_id}/no_task_id")
        assert task_info.status_code == 404
