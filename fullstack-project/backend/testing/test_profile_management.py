from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# helper to register a user and log in, returns the auth token and user id
def register_and_login(email, password="Password123", role="customer"):
    client.post("/user", json={
        "email": email,
        "password": password,
        "name": "Test User",
        "age": 25,
        "gender": "male",
        "role": role
    })
    response = client.post("/user/login", json={"email": email, "password": password})
    data = response.json()
    return data.get("token"), data.get("user_id")


# viewing profile

def test_user_can_view_own_profile():
    token, user_id = register_and_login("viewprofile@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("email") == "viewprofile@example.com"
    assert data.get("age") == 25
    assert data.get("gender") == "male"
    assert data.get("role") == "customer"

def test_password_not_returned_in_profile():
    token, user_id = register_and_login("nopwdprofile@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    # password should never be returned
    assert "password" not in response.json()


# updating profile

def test_user_can_update_own_details():
    token, user_id = register_and_login("updateme@example.com")
    response = client.put(f"/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "updated@example.com",
            "name": "Updated Name",
            "age": 30,
            "gender": "other",
            "role": "customer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("email") == "updated@example.com"
    assert data.get("name") == "Updated Name"
    assert data.get("age") == 30
    assert data.get("gender") == "other"

def test_role_cannot_be_changed_by_user():
    token, user_id = register_and_login("rolechange@example.com")
    response = client.put(f"/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "rolechange@example.com",
            "name": "Test User",
            "age": 25,
            "gender": "male",
            "role": "admin"  # trying to upgrade to admin
        }
    )
    # role should stay as customer regardless
    assert response.status_code == 200
    assert response.json().get("role") == "customer"

def test_update_requires_authentication():
    _, user_id = register_and_login("noauthupdate@example.com")
    response = client.put(f"/user/{user_id}",
        json={
            "email": "hacked@example.com",
            "name": "Hacker",
            "age": 30,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422  # missing authorization header