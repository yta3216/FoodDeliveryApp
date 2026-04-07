""" testing favourite restaurants """

from fastapi.testclient import TestClient
import pytest
from app.main import app
from testing.test_cart_management import customer_with_token, manager_with_token
from testing.test_restaurant_crud import setup_restaurant

client = TestClient(app)

def test_get_favourites_empty(customer_with_token):
    token = customer_with_token["token"]
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == []

def test_get_favourites_requires_auth():
    res = client.get("/user/me/favourites")
    assert res.status_code == 401

def test_get_favourites_customer_only(manager_with_token):
    token = manager_with_token["token"]
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_add_favourite(customer_with_token, setup_restaurant):
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    assert restaurant_id in res.json()

def test_add_favourite_not_found(customer_with_token):
    token = customer_with_token["token"]
    res = client.post("/user/me/favourites/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_add_favourite_duplicate(customer_with_token, setup_restaurant):
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 409

def test_add_favourite_requires_auth():
    res = client.post("/user/me/favourites/1")
    assert res.status_code == 401

def test_add_favourite_customer_only(manager_with_token, setup_restaurant):
    token = manager_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    res = client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_remove_favourite(customer_with_token, setup_restaurant):
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.delete(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert restaurant_id not in res.json()

def test_remove_favourite_not_in_list(customer_with_token, setup_restaurant):
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    res = client.delete(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_remove_favourite_requires_auth():
    res = client.delete("/user/me/favourites/1")
    assert res.status_code == 401

def test_get_favourites_returns_restaurant_objects(customer_with_token, setup_restaurant):
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant["restaurant"]["id"]
    client.post(f"/user/me/favourites/{restaurant_id}", headers={"Authorization": f"Bearer {token}"})
    res = client.get("/user/me/favourites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == restaurant_id