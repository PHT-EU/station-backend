from fastapi.testclient import TestClient


from station.app.main import app
from station.app.api.dependencies import get_db

from .test_db import override_get_db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_data_set_create():
    response = client.post("/api/datasets", json={
        "name": "test data set",
        "data_type": "tabular",
        "storage_type": "fhir"

    })

    assert response.status_code == 200, response.text

    data = response.json()
    dataset_id = data["id"]
    assert dataset_id


def test_data_set_get():
    response = client.get(f"/api/datasets/{1}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["name"] == "test data set"


def test_get_all_data_sets():
    response = client.get("/api/datasets")
    assert response.status_code == 200, response.text
    data = response.json()

    assert len(data) >= 1
