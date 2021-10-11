import pytest
from fastapi.testclient import TestClient

from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_get_master_images():
    response = client.get("/api/local_trains/master_images")
    assert response.status_code == 200, response.json