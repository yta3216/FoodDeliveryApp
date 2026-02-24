"""testing general user creation."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_user():
    response=client.post(
        "/user", 
        json={
            "email": "test@example.com", 
            "password": "passwordpassword",
            "name": "John Smith",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
        )
    assert response.status_code == 201
    # we can't predict the user ID, but we can check others
    assert response.json().get("email") == "test@example.com"
    assert response.json().get("password") == "passwordpassword"
    assert response.json().get("name") == "John Smith"
    assert response.json().get("age") == 25
    assert response.json().get("gender") == "male"
    assert response.json().get("role") == "customer"
    assert response.json().get("reset_token") is None
    assert response.json().get("reset_token_expiry") is None
