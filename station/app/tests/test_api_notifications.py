import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv, find_dotenv

from station.app.main import app
from station.app.api.dependencies import get_db
from station.app.crud.crud_notifications import notifications
from station.app.schemas.notifications import NotificationCreate
from station.app.config import settings

from .test_db import override_get_db, TestingSessionLocal

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_notification_create():
    """
    Test the creation of a Notification
    """
    response = client.post("/api/notifications", json={"topic": "Test Notification", "message": "testing"})
    assert response.status_code == 201
    assert response.json()["topic"] == "Test Notification"
    assert response.json()["message"] == "testing"


def test_notification_create_fail():
    """
    Test the creation of a Notification --fail
    """
    response = client.post("/api/notification/x", json={"topic": "Test Notification", "message": "testing"})
    assert response.status_code == 404, response.text


def test_notification_get_by_id():
    """
    Test the retrieval of a Notification
    """
    response = client.get(f"/api/notifications/1")
    assert response.status_code == 200
    assert response.json()["topic"] == "Test Notification"
    assert response.json()["message"] == "testing"


def test_notification_get_by_id_fail():
    """
    Test the retrieval of a Notification --fail
    """
    response = client.get(f"/api/notification/x")
    assert response.status_code == 404, response.text

def test_notification_update():
    """
    Test the update of a Notification
    """
    response = client.put("/api/notifications/1", json={'message': 'testing', 'topic': 'Test Notification Updated', 'is_read': True})
    assert response.status_code == 200
    assert response.json()["topic"] == "Test Notification Updated"
    assert response.json()["message"] == "testing"


def test_get_list_notifications():
    """
    Test the retrieval of a list of Notifications
    """
    response = client.post("/api/notifications", json={"topic": "Test Notification 2", "message": "testing"})
    assert response.status_code == 201
    assert response.json()["topic"] == "Test Notification 2"
    assert response.json()["message"] == "testing"
    response = client.get(f"/api/notifications")
    assert response.status_code == 200
    assert len(response.json()) >= 1



def test_notification_delete():
    """
    Test the deletion of a Notification
    """
    response = client.delete("/api/notifications/1")
    assert response.status_code == 202, response.text

