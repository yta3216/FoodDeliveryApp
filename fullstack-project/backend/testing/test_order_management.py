"""Test cases for order management"""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from app.services.user_service import get_customer
from app.services.restaurant_service import get_restaurant_by_id
from testing.test_restaurant_crud import setup_restaurant
from testing.test_cart_management import customer_with_cart_and_token, customer_with_token, setup_restaurant_menu

client = TestClient(app)

# --------------- TESTS -------------- #

def test_place_order(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer_id"]
    token = customer_with_cart_and_token["token"]
    restaurant = customer_with_cart_and_token["restaurant_id"]

    response = client.post("/order", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    
    new_order = response.json()
    assert new_order["customer_id"] == customer
    assert new_order["restaurant_id"] == restaurant
    assert new_order["status"] == "pending"
    assert new_order["subtotal"] == 2 * 9.99 + 1 * 10.99
    assert len(new_order["items"]) == 2

def test_get_orders_for_customer(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer_id"]
    token = customer_with_cart_and_token["token"]
    restaurant = customer_with_cart_and_token["restaurant_id"]

    client.post("/order", headers={"Authorization": f"Bearer {token}"})

    response = client.get("/order/customer", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == 1
    for order in orders:
        assert order["customer_id"] == customer
        assert order["restaurant_id"] == restaurant
        assert order["status"] == "pending"
        assert order["subtotal"] == 2 * 9.99 + 1 * 10.99
        assert len(order["items"]) == 2

def test_place_order_with_empty_cart(customer_with_token):
    token = customer_with_token["token"]
    response = client.post("/order", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400