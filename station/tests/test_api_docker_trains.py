from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)



def test_docker_train_create():
    response = client.post("/api/trains/docker/", json={
        "train_id": "test_train"

    })

    assert response.status_code == 200, response.text
