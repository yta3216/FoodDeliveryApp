from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# helper to register a user and log in, returns the auth token + user id
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


# view user details

def test_user_can_view_own_details():
    token, user_id = register_and_login("viewown@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json().get("id") == user_id

def test_customer_cannot_view_other_user_details():
    # create two users, try to view each other's details
    token1, user_id1 = register_and_login("customer1auth@example.com")
    token2, user_id2 = register_and_login("customer2auth@example.com")

    # customer1 tries to view customer2's details (should be blocked)
    response = client.get(f"/user/{user_id2}", headers={"Authorization": f"Bearer {token1}"})
    assert response.status_code == 403

def test_manager_cannot_view_other_user_details():
    token_manager, _ = register_and_login("managerauth@example.com", role="manager")
    _, customer_id = register_and_login("managertarget@example.com")

    # manager tries to view a different user's details
    response = client.get(f"/user/{customer_id}", headers={"Authorization": f"Bearer {token_manager}"})
    assert response.status_code == 403

def test_no_token_cannot_view_user_details():
    _, user_id = register_and_login("notoken@example.com")
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 422  # missing required Authorization header

def test_invalid_token_cannot_view_user_details():
    _, user_id = register_and_login("invalidtoken@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": "Bearer faketoken123"})
    assert response.status_code == 401


# editing user details

def test_customer_cannot_edit_other_user():
    token1, _ = register_and_login("editcustomer1@example.com")
    _, user_id2 = register_and_login("editcustomer2@example.com")

    response = client.put(f"/user/{user_id2}", 
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "email": "hacked@example.com",
            "password": "hacked123",
            "name": "Hacker",
            "age": 30,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 403

def test_manager_cannot_edit_other_user():
    token_manager, _ = register_and_login("editmanager@example.com", role="manager")
    _, customer_id = register_and_login("editmanagertarget@example.com")

    response = client.put(f"/user/{customer_id}",
        headers={"Authorization": f"Bearer {token_manager}"},
        json={
            "email": "hacked@example.com",
            "password": "hacked123",
            "name": "Hacker",
            "age": 30,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 403