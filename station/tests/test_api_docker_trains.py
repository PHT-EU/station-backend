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
    return "test_train"


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
    response = client.post("/api/trains/docker", json={
        "train_id": train_id

    })

    assert response.status_code == 400, response.text


def test_get_train_by_id(train_id):
    response = client.get(f"/api/trains/docker/{train_id}")
    assert response.status_code == 200, response.text


def test_list_docker_trains():
    response = client.get("/api/trains/docker")

    assert response.status_code == 200, response.text

    assert len(response.json()) == 1
