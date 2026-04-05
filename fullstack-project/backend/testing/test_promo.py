"""Minimal test cases for promotional code functionality."""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.user_schema import UserRole
from app.repositories.promo_repo import load_promo_codes, save_promo_codes

client = TestClient(app)

DATA_PATH = Path(__file__).resolve().parents[1] / "app" / "data"

def seed_promo(overrides: dict = {}) -> dict:
    """Seeds a single promo code into promo_codes.json for testing."""
    base = {
        "id": 1,
        "code": "TEST10",
        "description": "Test promo",
        "type": "fixed_amount",
        "value": 10.0,
        "min_order_value": 0.0,
        "expiry_date": None,
        "is_active": True,
        "is_public": True,
        "is_first_order_only": False,
        "used_by_customer_ids": []
    }
    promo = {**base, **overrides}
    save_promo_codes([promo])
    return promo

def create_and_login(email: str, role: str) -> dict:
    """Creates a user and returns their id and auth token."""
    res = client.post("/user", json={
        "email": email,
        "password": "testpassword",
        "name": "Test User",
        "age": 25,
        "gender": "male",
        "role": role
    })
    assert res.status_code == 201
    login = client.post("/user/login", json={"email": email, "password": "testpassword"})
    assert login.status_code == 200
    return {"id": res.json()["id"], "token": login.json()["token"]}

@pytest.fixture
def customer():
    return create_and_login("promo_customer@test.com", UserRole.CUSTOMER.value)

@pytest.fixture
def admin():
    return create_and_login("promo_admin@test.com", UserRole.ADMIN.value)

def test_get_public_promos(customer):
    seed_promo()
    response = client.get("/promo")
    assert response.status_code == 200
    codes = [p["code"] for p in response.json()]
    assert "TEST10" in codes

def test_inactive_promo_not_in_public_list(customer):
    seed_promo({"is_active": False})
    response = client.get("/promo")
    assert response.status_code == 200
    assert all(p["code"] != "TEST10" for p in response.json())

def test_admin_get_all_promos(admin):
    seed_promo({"is_active": False})
    response = client.get("/promo/all", headers={"Authorization": f"Bearer {admin['token']}"})
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_customer_cannot_get_all_promos(customer):
    response = client.get("/promo/all", headers={"Authorization": f"Bearer {customer['token']}"})
    assert response.status_code == 403

def test_admin_create_promo(admin):
    response = client.post(
        "/promo",
        json={
            "code": "NEWCODE",
            "description": "New test promo",
            "type": "fixed_amount",
            "value": 5.0,
            "min_order_value": 0.0,
            "is_public": True,
            "is_first_order_only": False
        },
        headers={"Authorization": f"Bearer {admin['token']}"}
    )
    assert response.status_code == 201
    assert response.json()["code"] == "NEWCODE"
    assert response.json()["is_active"] is True

def test_customer_cannot_create_promo(customer):
    response = client.post(
        "/promo",
        json={"code": "HACK", "description": "", "type": "fixed_amount", "value": 99.0},
        headers={"Authorization": f"Bearer {customer['token']}"}
    )
    assert response.status_code == 403

def test_apply_valid_promo(customer):
    seed_promo()
    response = client.post(
        "/promo/apply",
        json={"code": "TEST10"},
        headers={"Authorization": f"Bearer {customer['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["promo_code"] == "TEST10"

def test_apply_nonexistent_promo(customer):
    response = client.post(
        "/promo/apply",
        json={"code": "FAKECODE"},
        headers={"Authorization": f"Bearer {customer['token']}"}
    )
    assert response.status_code == 404

def test_apply_inactive_promo(customer):
    seed_promo({"is_active": False})
    response = client.post(
        "/promo/apply",
        json={"code": "TEST10"},
        headers={"Authorization": f"Bearer {customer['token']}"}
    )
    assert response.status_code == 400

def test_remove_promo(customer):
    seed_promo()
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {customer['token']}"})
    response = client.delete("/promo/remove", headers={"Authorization": f"Bearer {customer['token']}"})
    assert response.status_code == 200
    assert response.json()["promo_code"] is None

def test_expired_promo_rejected_and_deactivated(customer, setup_restaurant_with_items):
    seed_promo({"expiry_date": "2000-01-01"})
    restaurant = setup_restaurant_with_items["restaurant"]
    item_id = setup_restaurant_with_items["item_id"]
    token = customer["token"]

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {token}"})

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 400
    assert "expired" in receipt_response.json()["detail"].lower()

    promo = load_promo_codes()[0]
    assert promo["is_active"] is False

def test_min_order_value_not_met(customer, setup_restaurant_with_items):
    seed_promo({"min_order_value": 999.0})
    restaurant = setup_restaurant_with_items["restaurant"]
    item_id = setup_restaurant_with_items["item_id"]
    token = customer["token"]

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {token}"})

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 400
    assert "minimum order value" in receipt_response.json()["detail"].lower()

def test_discount_applied_to_receipt(customer, setup_restaurant_with_items):
    seed_promo({"value": 5.0})
    restaurant = setup_restaurant_with_items["restaurant"]
    item_id = setup_restaurant_with_items["item_id"]
    token = customer["token"]

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {token}"})

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt = receipt_response.json()
    assert receipt["discount"] == 5.0
    assert receipt["promo_code"] == "TEST10"
    assert receipt["total"] == round(receipt["subtotal"] + receipt["tax"] + receipt["delivery_fee"] - 5.0, 2)

def test_checkout_deactivates_promo(customer, setup_restaurant_with_items):
    seed_promo()
    restaurant = setup_restaurant_with_items["restaurant"]
    item_id = setup_restaurant_with_items["item_id"]
    token = customer["token"]

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {token}"})

    client.patch("/payment/topup-wallet", json={
        "amount": 100.0, "card_number": "1234567890123456",
        "expiry_month": 12, "expiry_year": 2099, "cvv": "123", "cardholder_name": "Test"
    }, headers={"Authorization": f"Bearer {token}"})

    receipt_id = client.get("/receipt", headers={"Authorization": f"Bearer {token}"}).json()["id"]
    checkout = client.post("/payment/checkout", json={"receipt_id": receipt_id}, headers={"Authorization": f"Bearer {token}"})
    assert checkout.status_code == 201

    promo = load_promo_codes()[0]
    assert promo["is_active"] is False
    assert customer["id"] in promo["used_by_customer_ids"]

def test_first_order_only_rejected_on_second_order(customer, setup_restaurant_with_items):
    seed_promo({"is_first_order_only": True})
    restaurant = setup_restaurant_with_items["restaurant"]
    item_id = setup_restaurant_with_items["item_id"]
    token = customer["token"]

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.patch("/payment/topup-wallet", json={
        "amount": 100.0, "card_number": "1234567890123456",
        "expiry_month": 12, "expiry_year": 2099, "cvv": "123", "cardholder_name": "Test"
    }, headers={"Authorization": f"Bearer {token}"})
    receipt_id = client.get("/receipt", headers={"Authorization": f"Bearer {token}"}).json()["id"]
    client.post("/payment/checkout", json={"receipt_id": receipt_id}, headers={"Authorization": f"Bearer {token}"})

    client.patch(f"/cart/{restaurant.id}", headers={"Authorization": f"Bearer {token}"})
    client.post("/cart/item", json={"menu_item_id": item_id, "qty": 1}, headers={"Authorization": f"Bearer {token}"})
    client.post("/promo/apply", json={"code": "TEST10"}, headers={"Authorization": f"Bearer {token}"})

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 400
    assert "first order" in receipt_response.json()["detail"].lower()

def test_admin_deactivate_promo(admin):
    seed_promo()
    response = client.patch(
        "/promo/1/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

def test_admin_reactivate_promo(admin):
    seed_promo({"is_active": False})
    response = client.patch(
        "/promo/1/status",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin['token']}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

@pytest.fixture
def setup_restaurant_with_items(admin):
    """Creates a restaurant with one menu item via the API."""
    from app.services.restaurant_service import get_restaurant_by_id

    manager = create_and_login("promo_manager@test.com", UserRole.RESTAURANT_MANAGER.value)
    token = manager["token"]

    restaurant_res = client.post("/restaurant", json={
        "name": "Promo Test Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "123 Test St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V1V 1V1"
        },
        "delivery_fee": 2.00,
        "max_delivery_radius_km": 20.0
    }, headers={"Authorization": f"Bearer {token}"})
    assert restaurant_res.status_code == 201

    restaurant_id = restaurant_res.json()["id"]
    menu_res = client.post(
        f"/restaurant/{restaurant_id}/menu",
        json={"name": "Test Item", "price": 15.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert menu_res.status_code == 201

    restaurant = get_restaurant_by_id(restaurant_id)
    return {
        "restaurant": restaurant,
        "item_id": restaurant.menu.items[0].id
    }