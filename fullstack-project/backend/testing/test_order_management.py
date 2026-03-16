"""Test cases for order management"""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from app.services.user_service import get_customer
from app.services.restaurant_service import get_restaurant_by_id
from app.services.receipt_service import get_receipt
from testing.test_restaurant_crud import setup_restaurant
from testing.test_cart_management import customer_with_cart_and_token, customer_with_token, setup_restaurant_menu

client = TestClient(app)

# Helper: creates receipt->sucessful payment -> order created
def place_order(token: str) -> dict:
    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt_id = receipt_response.json()["id"]
 
    checkout_response = client.post(
        "/payment/checkout",
        json={
            "receipt_id": receipt_id,
            "card_number": "1234567890123456",
            "expiry_month": 12,
            "expiry_year": 2099,
            "cvv": "123",
            "cardholder_name": "Test Customer"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert checkout_response.status_code == 201
    return checkout_response.json()["order"]

# --------------- TESTS -------------- #

# --- Customer --- #
def test_place_order(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer_id"]
    token = customer_with_cart_and_token["token"]
    restaurant = customer_with_cart_and_token["restaurant_id"]
    
    order = place_order(token)

    assert order["customer_id"] == customer
    assert order["restaurant_id"] == restaurant
    assert order["status"] == "pending"
    assert order["receipt_id"] != 0
    assert len(get_receipt(order["receipt_id"]).items) == 2

def test_place_order_with_empty_cart(customer_with_token):
    token = customer_with_token["token"]
    response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400

def test_get_orders_for_customer(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer_id"]
    token = customer_with_cart_and_token["token"]
    restaurant = customer_with_cart_and_token["restaurant_id"]

    place_order(token)

    response = client.get("/order/customer", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == 1
    for order in orders:
        assert order["customer_id"] == customer
        assert order["restaurant_id"] == restaurant
        assert order["status"] == "pending"
        assert order["receipt_id"] != 0
        assert len(get_receipt(order["receipt_id"]).items) == 2

def test_get_orders_for_customer_with_no_orders(customer_with_token):
    token = customer_with_token["token"]
    response = client.get("/order/customer", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == 0

# --- Restaurant --- #

def test_get_orders_for_restaurant(customer_with_cart_and_token, setup_restaurant_menu):
    customer = customer_with_cart_and_token["customer_id"]
    token = customer_with_cart_and_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]["id"]
    manager_token = setup_restaurant_menu["token"]

    place_order(token)

    response = client.get(f"/order/restaurant/{restaurant}", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 200

    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == 1
    for order in orders:
        assert order["customer_id"] == customer
        assert order["restaurant_id"] == restaurant
        assert order["status"] == "pending"
        assert order["receipt_id"] != 0
        assert len(get_receipt(order["receipt_id"]).items) == 2

def test_get_orders_for_restaurant_unauthorized(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]["id"]

    response = client.get(f"/order/restaurant/{restaurant}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

def test_get_orders_for_fake_restaurant(setup_restaurant_menu):
    manager_token = setup_restaurant_menu["token"]
    fake_restaurant = 6767

    response = client.get(f"/order/restaurant/{fake_restaurant}", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 404