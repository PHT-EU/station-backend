import pytest
import os
from fastapi.testclient import TestClient

from station.app.main import app
from station.app.api.dependencies import get_db
from dotenv import load_dotenv, find_dotenv

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def train_id():
    load_dotenv(find_dotenv())
    return "testTrain"


@pytest.fixture
def docker_train_config():
    config = {
        "name": "test_config",
        "airflow_config": {
            "env": [{
                "key": "FHIR_ADDRESS",
                "value": "test_address"
            }
            ],
            "volumes": [{
                "host_path": "path/on/host",
                "container_path": "path/in/container",
                "mode": "ro"
            }],
            "repository": "example/repository",
            "tag": "latest"
        },

        "auto_execute": True
    }

    return config


def test_docker_train_create(train_id):
    response = client.post("/api/trains/docker", json={
        "train_id": train_id

    })

    assert response.status_code == 200, response.text

    json_response = response.json()
    assert json_response["train_id"] == train_id
    print(json_response)
    assert json_response["state"]["num_executions"] == 0
    assert json_response["state"]["status"] == "inactive"


def test_docker_train_create_fails(train_id):
    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": train_id

        }
    )

    assert response.status_code == 400, response.text


def test_get_train_by_id(train_id):
    response = client.get(f"/api/trains/docker/{train_id}")
    assert response.status_code == 200, response.text


def test_get_train_by_id_fails():
    response = client.get("/api/trains/docker/notthere")
    assert response.status_code == 404, response.text


def test_list_docker_trains():
    response = client.get("/api/trains/docker")

    assert response.status_code == 200, response.text

    assert len(response.json()) == 1


def test_docker_train_config_create(docker_train_config):
    response = client.post(
        "/api/trains/docker/config",
        json=docker_train_config
    )
    assert response.status_code == 200, response.text

    assert response.json()["name"] == docker_train_config["name"]
    assert response.json()["auto_execute"]


def test_docker_train_config_create_fails(docker_train_config):
    response = client.post(
        "/api/trains/docker/config",
        json=docker_train_config
    )
    assert response.status_code == 400


def test_get_docker_train_configs():
    response = client.get("/api/trains/docker/configs/all")
    assert response.status_code == 200, response.text
    assert len(response.json()) >= 1


def test_get_docker_train_config_by_id():
    response = client.get("/api/trains/docker/config/1")
    assert response.status_code == 200, response.text


def test_get_docker_train_config_by_id_fails():
    response = client.get("/api/trains/docker/config/234")
    assert response.status_code == 404, response.text


def test_update_docker_train_config(docker_train_config):
    docker_train_config["name"] = "updated name"
    response = client.put("/api/trains/docker/config/1",
                          json=docker_train_config)

    assert response.status_code == 200, response.text
    response = client.get("/api/trains/docker/config/1")

    assert response.json()["name"] == "updated name"


def test_update_docker_train_config_fails(docker_train_config):
    docker_train_config["name"] = "updated name"
    response = client.put("/api/trains/docker/config/234",
                          json=docker_train_config)
    assert response.status_code == 404, response.text


def test_assign_docker_train_config(train_id):
    response = client.post(f"/api/trains/docker/{train_id}/config/1")
    assert response.status_code == 200, response.text
    response = client.get(f"/api/trains/docker/{train_id}")

    assert response.json()["config_id"] == 1

    # test non existing config error
    response = client.post(f"/api/trains/docker/{train_id}/config/321")

    assert response.status_code == 404

    # test non existing train error

    response = client.post("/api/trains/docker/no_train/config/1")
    assert response.status_code == 404


def test_get_config_for_train(train_id):
    response = client.get(f"/api/trains/docker/{train_id}/config")
    assert response.status_code == 200, response.text
    assert len(response.json()["trains"]) == 1

    new_train_id = "no_config_train"
    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": new_train_id

        }
    )
    assert response.status_code == 200
    response = client.get(f"/api/trains/docker/{new_train_id}/config")

    assert response.status_code == 404


def test_create_train_with_config(docker_train_config):
    # assign existing config
    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": "with_existing_config",
            "config": 1
        }
    )
    assert response.status_code == 200, response.text
    config_response = client.get(f"/api/trains/docker/with_existing_config/config")
    assert config_response.json()["name"] == "updated name"
    assert len(config_response.json()["trains"]) == 2

    # fails with unknown config id
    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": "config does not exist",
            "config": 3213
        }
    )
    assert response.status_code == 404, response.text

    new_config = {
        "name": "new config",
        "airflow_config": {
            "env": [{
                "key": "FHIR_ADDRESS",
                "value": "test_address"
            }
            ],
            "volumes": [{
                "host_path": "path/on/host",
                "container_path": "path/in/container",
                "mode": "ro"
            }]

        },

        "auto_execute": False
    }

    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": "with_new_config",
            "name": "train with new config",
            "config": new_config
        }
    )
    assert response.status_code == 200
    print(response.json())

    config_response = client.get(f"/api/trains/docker/with_new_config/config")
    assert config_response.json()["name"] == "new config"


def test_get_train_state():
    train_id = "test_train_state"
    response = client.post(
        "/api/trains/docker",
        json={
            "train_id": train_id,
        }
    )
    assert response.status_code == 200, response.text

    response = client.get(f"/api/trains/docker/{train_id}/state")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "inactive"


def test_update_train_state(train_id):
    response = client.put(f"/api/trains/docker/{train_id}/state", json={"status": "active", "num_executions": 1})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "active"
    assert response.json()["num_executions"] == 1


def test_synchronize_database():
    if os.getenv("ENVIRONMENT") == "testing":
        response_nostation = client.get("/api/trains/docker/sync")
        assert response_nostation.status_code == 200, response_nostation.text

        response = client.get("/api/trains/docker/sync/?station_id=1")
        if os.getenv("STATION_ID") == 1:
            assert len(response.json()) == 0
        assert response.status_code == 200, response.text


def test_synchronize_database_fails():
    if os.getenv("ENVIRONMENT") == "testing":
        response = client.get("/api/trains/docker/sync/?station_id=123")
        assert response.status_code == 404, response.text


def test_run_docker_train(train_id, docker_train_config):
    if os.getenv("ENVIRONMENT") == "testing":
        old_state = client.get(f"/api/trains/docker/{train_id}/state")

        # run with given config id
        response = client.post(f"/api/trains/docker/{train_id}/run", json={"config_id": 1})
        assert response.json()["airflow_dag_run"]
        assert response.json()["config"] == 1
        assert response.status_code == 200, response.text

        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        assert old_state.json() != state_response.json()
        assert old_state.json()["num_executions"] + 1 == state_response.json()["num_executions"]

        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert execution_response.json()[-1]["airflow_dag_run"] == response.json()["airflow_dag_run"]

        # run with default config
        response = client.post(f"/api/trains/docker/{train_id}/run",
                               json={"config_id": "default"})
        assert response.json()["airflow_dag_run"]
        assert response.json()["config"] is None
        assert response.status_code == 200, response.text

        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        assert old_state.json()["num_executions"] + 2 == state_response.json()["num_executions"]

        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert execution_response.json()[-1]["airflow_dag_run"] == response.json()["airflow_dag_run"]

        # run with config assigned to train
        response = client.post(f"/api/trains/docker/{train_id}/run")
        assert response.json()["airflow_dag_run"]
        assert response.json()["config"] == 1
        assert response.status_code == 200, response.text

        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        assert old_state.json()["num_executions"] + 3 == state_response.json()["num_executions"]

        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert execution_response.json()[-1]["airflow_dag_run"] == response.json()["airflow_dag_run"]


def test_run_docker_train_fails(train_id, docker_train_config):
    old_state = client.get(f"/api/trains/docker/{train_id}/state")
    old_executions = client.get(f"/api/trains/docker/{train_id}/executions")

    if os.getenv("ENVIRONMENT") == "testing":

        # no config with id given
        response = client.post(f"/api/trains/docker/{train_id}/run", json={"config_id": 4})
        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert old_state.json() == state_response.json()
        assert old_executions.json() == execution_response.json()
        assert response.status_code == 400, response.text

        # no tag and no repository given
        response = client.post(f"/api/trains/docker/{train_id}/run", json={"config_id": 2})
        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert old_state.json() == state_response.json()
        assert old_executions.json() == execution_response.json()
        assert response.status_code == 400, response.text

        # train not defined
        response = client.post(f"/api/trains/docker/no_train/run", json={"config_id": 1})
        assert response.status_code == 404, response.text

    else:
        response = client.post(f"/api/trains/docker/{train_id}/run", json={"config_id": "default"})
        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert old_state.json() == state_response.json()
        assert old_executions.json() == execution_response.json()
        assert response.status_code == 503, response.text

        response = client.post(f"/api/trains/docker/{train_id}/run")
        state_response = client.get(f"/api/trains/docker/{train_id}/state")
        execution_response = client.get(f"/api/trains/docker/{train_id}/executions")
        assert old_state.json() == state_response.json()
        assert old_executions.json() == execution_response.json()
        assert response.status_code == 503, response.text
