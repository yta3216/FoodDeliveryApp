import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login_customer():
    client.post("/user", json={
        "name": "Fav Tester",
        "email": "fav@test.com",
        "password": "password123",
        "age": 22,
        "gender": "prefer not to say",
        "role": "customer"
    })
    res = client.post("/user/login", json={
        "email": "fav@test.com",
        "password": "password123"
    })
    return res.json()["token"]


def register_and_login_manager():
    client.post("/user", json={
        "name": "Fav Manager",
        "email": "favmanager@test.com",
        "password": "password123",
        "age": 30,
        "gender": "prefer not to say",
        "role": "manager"
    })
    res = client.post("/user/login", json={
        "email": "favmanager@test.com",
        "password": "password123"
    })
    return res.json()["token"]


def create_restaurant(manager_token):
    res = client.post("/restaurant", json={
        "name": "Fav Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "123 Test St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B1A1"
        }
    }, headers={"Authorization": f"Bearer {manager_token}"})
    return res.json()["id"]


# --- GET /user/me/favourites ---

def test_get_favourites_empty():
    token = register_and_login_customer()
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == []

def test_get_favourites_requires_auth():
    res = client.get("/user/me/favourites")
    assert res.status_code == 401

def test_get_favourites_customer_only():
    manager_token = register_and_login_manager()
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {manager_token}"})
    assert res.status_code == 403


# --- POST /user/me/favourites/{restaurant_id} ---

def test_add_favourite():
    token = register_and_login_customer()
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    assert restaurant_id in res.json()

def test_add_favourite_not_found():
    token = register_and_login_customer()
    res = client.post("/user/me/favourites/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_add_favourite_duplicate():
    token = register_and_login_customer()
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 409

def test_add_favourite_requires_auth():
    res = client.post("/user/me/favourites/1")
    assert res.status_code == 401

def test_add_favourite_customer_only():
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert res.status_code == 403


# --- DELETE /user/me/favourites/{restaurant_id} ---

def test_remove_favourite():
    token = register_and_login_customer()
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.delete(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert restaurant_id not in res.json()

def test_remove_favourite_not_in_list():
    token = register_and_login_customer()
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    res = client.delete(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_remove_favourite_requires_auth():
    res = client.delete("/user/me/favourites/1")
    assert res.status_code == 401


# --- GET /user/me/favourites after adding ---

def test_get_favourites_returns_restaurant_objects():
    token = register_and_login_customer()
    manager_token = register_and_login_manager()
    restaurant_id = create_restaurant(manager_token)
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == restaurant_id