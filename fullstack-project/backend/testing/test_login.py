"""testing user login."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# create a test user
def create_test_user():
    response=client.post(
        "/user", 
        json={
            "email": "test@example.com", 
            "password": "Password123",
            "name": "John Smith",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 201
    return response.json()

# testing with a valid email and password
def test_login_correct_details():
    user = create_test_user()

    response = client.post(
        "/user/login",
        json = {
            "email": user.get("email"),
            "password": "Password123"
        },
    )

    assert response.status_code == 200
    returned_data = response.json()

    # check returned data; should match user
    assert "token" in returned_data

    assert returned_data.get("email") == user.get("email")
    assert returned_data.get("role") == user.get("role")
    assert returned_data.get("name") == user.get("name")
    assert returned_data.get("age") == user.get("age")
    assert returned_data.get("gender") == user.get("gender")

# testing with a valid email but incorrect password
def test_login_wrong_password():
    user = create_test_user()

    response = client.post(
        "/user/login",
        json = {
            "email": user.get("email"),
            "password": "wrongpassword"
        },
    )

    assert response.status_code == 401
    assert response.json.get("detail") == "Invalid email or password"

# testing with an invalid email
def test_login_wrong_email():
    response = client.post(
        "/user/login",
        json = {
            "email": "wrongemail@example.com",
            "password": "wrongpassword"
        },
    )

    assert response.status_code == 401
    assert response.json.get("detail") == "Invalid email or password"