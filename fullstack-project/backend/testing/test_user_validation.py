"""testing user signup input validation."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_email():
    response = client.post(
        "/user",
        json={
            "email": "invalidemail",
            "password": "password123",
            "name": "Test User",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    fields = [e["loc"][-1] for e in errors]
    assert "email" in fields

def test_invalid_age_too_low():
    response = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "age": -1,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    fields = [e["loc"][-1] for e in errors]
    assert "age" in fields

def test_invalid_age_too_high():
    response = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "age": 200,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422

def test_invalid_gender():
    response = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "Test User",
            "age": 25,
            "gender": "banana",
            "role": "customer"
        }
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    fields = [e["loc"][-1] for e in errors]
    assert "gender" in fields

def test_empty_name():
    response = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "password123",
            "name": "   ",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422

def test_password_too_short():
    response = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "1234",
            "name": "Test User",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 422

def test_valid_user_creation():
    response = client.post(
        "/user",
        json={
            "email": "validuser@example.com",
            "password": "password123",
            "name": "Valid User",
            "age": 25,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 201

def test_valid_gender():
    for gender in ["male", "female", "other", "prefer not to say"]:
        response = client.post(
            "/user",
            json={
                "email": f"{gender.replace(' ', '')}@example.com",
                "password": "password123",
                "name": "Test User",
                "age": 25,
                "gender": gender,
                "role": "customer"
            }
        )
        assert response.status_code == 201