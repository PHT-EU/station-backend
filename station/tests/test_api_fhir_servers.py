import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv, find_dotenv

from station.app.main import app
from station.app.api.dependencies import get_db
from station.app.crud.crud_fhir_servers import fhir_servers
from station.app.schemas.fhir import FHIRServerCreate
from station.app.config import Settings

from .test_db import override_get_db, TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture()
def station_settings():
    load_dotenv(find_dotenv())
    settings = Settings()
    settings.setup()
    return settings


def test_fhir_server_encrypted_storage(station_settings):
    load_dotenv(find_dotenv())

    db = TestingSessionLocal()

    obj_in = {"name": "Test Server", "api_address": "http://test.com", "username": "user", "password": "password"}
    obj_in = FHIRServerCreate(**obj_in)
    fhir_server = fhir_servers.create(db, obj_in=obj_in)

    station_fernet = station_settings.get_fernet()
    assert fhir_server.name == "Test Server"
    assert fhir_server.password != "password"
    assert station_fernet.decrypt(fhir_server.password.encode()) == b"password"

    db.close()


def test_fhir_server_create():
    """
    Test the creation of a FHIR server
    """
    response = client.post("/api/fhir/server", json={"name": "Test Server", "api_address": "http://test.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Server"
    assert response.json()["api_address"] == "http://test.com"


def test_fhir_server_get():
    """
    Test the retrieval of a FHIR server
    """
    response = client.get("/api/fhir/server/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Server"
    assert response.json()["api_address"] == "http://test.com"


def test_list_fhir_servers():
    """
    Test the retrieval of a list of FHIR servers
    """
    response = client.post("/api/fhir/server", json={"name": "Test Server", "api_address": "http://test.com"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Server"
    assert response.json()["api_address"] == "http://test.com"
    response = client.get("/api/fhir/server")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Test Server"
    assert response.json()[0]["api_address"] == "http://test.com"


def test_update_fhir_server():
    """
    Test the update of a FHIR server
    """
    response = client.put("/api/fhir/server/1",
                          json={"name": "Test Server Updated", "api_address": "http://test.com", "username": "user",
                                "password": "password"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Server Updated"
    assert response.json()["api_address"] == "http://test.com"


def test_delete_fhir_server():
    """
    Test the deletion of a FHIR server
    """
    response = client.delete("/api/fhir/server/1")
    assert response.status_code == 202
