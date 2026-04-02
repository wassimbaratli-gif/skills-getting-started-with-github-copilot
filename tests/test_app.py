import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as original_activities


@pytest.fixture(autouse=True)
def reset_activities():
    # Ensure each test gets a fresh in-memory state to avoid cross-test side effects.
    app.dependency_overrides.clear()
    original_snapshot = copy.deepcopy(original_activities)
    from src import app as app_module

    app_module.activities = original_snapshot
    yield
    app_module.activities = original_snapshot


client = TestClient(app)


def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_signup_for_activity_success():
    email = "teststudent@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}

    all_activities = client.get("/activities").json()
    assert email in all_activities["Chess Club"]["participants"]


def test_signup_for_activity_not_found():
    response = client.post("/activities/Nonexistent/signup", params={"email": "x@mergington.edu"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_already_signed_up():
    email = "michael@mergington.edu"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_success():
    email = "michael@mergington.edu"
    response = client.delete(f"/activities/Chess Club/participants/{email}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}

    all_activities = client.get("/activities").json()
    assert email not in all_activities["Chess Club"]["participants"]


def test_remove_participant_not_found_activity():
    response = client.delete("/activities/NotAnActivity/participants/test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_not_found_participant():
    response = client.delete("/activities/Chess Club/participants/nonexistent@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
