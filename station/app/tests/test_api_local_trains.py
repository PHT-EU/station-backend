import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import json

from requests import HTTPError

from station.app.main import app
from station.app.api.dependencies import get_db
import time
from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def train_id():
    response = client.post(
        "/api/local-trains",
        json={
            "name": "test_train",
            "custom_image": "test_image",
        }
    )
    return response.json()["id"]


def test_create_local_train():
    response = client.post(
        "/api/local-trains",
        json={
            "name": "test_train",
            "custom_image": "test_image",
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "test_train"


def test_get_local_train(train_id):
    response = client.get(f"/api/local-trains/{train_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test_train"


def test_update_local_train(train_id):
    response = client.put(
        f"/api/local-trains/{train_id}",
        json={
            "name": "test_train_updated",
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "test_train_updated"


def test_delete_local_train(train_id):
    response = client.delete(f"/api/local-trains/{train_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test_train"

    r = client.get(f"/api/local-trains/{train_id}")
    with pytest.raises(HTTPError):
        r.raise_for_status()
