import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def train_id():
    return "testTrain"


@pytest.fixture
def docker_train_config():
    config = {
        "name": "test_config",
        "airflow_config_json": {
            "env": {
                "FHIR_ADDRESS": "test_address"
            }
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

    assert json_response["state"]["num_executions"] == 0
    assert not json_response["state"]["status"]


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
    response = client.get(f"/api/trains/docker/configs/all")
    assert response.status_code == 200, response.text
    assert len(response.json()) >= 1


def test_get_docker_train_config_by_id():
    response = client.get(f"/api/trains/docker/config/1")
    assert response.status_code == 200, response.text

def test_get_docker_train_config_by_id_fails():
    response = client.get("/api/trains/docker/config/2")
    assert response.status_code == 404, response.text


def test_update_docker_train_config(docker_train_config):
    docker_train_config["name"] = "updated name"
    response = client.put("/api/trains/docker/config/1",
                          json=docker_train_config)

    assert response.status_code == 200, response.text
    response = client.get(f"/api/trains/docker/config/1")

    assert response.json()["name"] == "updated name"

def test_update_docker_train_config_fails(docker_train_config):
    docker_train_config["name"] = "updated name"
    response = client.put("/api/trains/docker/config/2",
                          json=docker_train_config)
    assert response.status_code == 404, response.text


def test_assign_docker_train_config(train_id):
    response = client.post(f"/api/trains/docker/{train_id}/config/1")
    assert response.status_code == 200, response.text
    response = client.get(f"/api/trains/docker/{train_id}")

    assert response.json()["config"]

    # test non existing config error
    response = client.post(f"/api/trains/docker/{train_id}/config/321")

    assert response.status_code == 404

    # test non existing train error

    response = client.post(f"/api/trains/docker/no_train/config/1")
    assert response.status_code == 404



def test_get_config_for_train(train_id):
    response = client.get(f"/api/trains/docker/{train_id}/config")
    assert response.status_code == 200, response.text

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
