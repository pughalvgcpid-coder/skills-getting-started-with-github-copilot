from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)
ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))
    return TestClient(app_module.app)


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_activity = INITIAL_ACTIVITIES[ACTIVITY_NAME]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[ACTIVITY_NAME] == expected_activity


def test_signup_adds_participant(client):
    # Arrange
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in app_module.activities[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    email = INITIAL_ACTIVITIES[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[ACTIVITY_NAME]["participants"].count(email) == 1


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_path = quote("Unknown Club", safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    email = INITIAL_ACTIVITIES[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {ACTIVITY_NAME}"}
    assert email not in app_module.activities[ACTIVITY_NAME]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_path = quote("Unknown Club", safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_nonparticipant(client):
    # Arrange
    email = "not.registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in app_module.activities[ACTIVITY_NAME]["participants"]


def test_root_redirects_to_frontend(client):
    # Arrange
    follow_redirects = False

    # Act
    response = client.get("/", follow_redirects=follow_redirects)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"