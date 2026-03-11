"""Test cases for order cancellation"""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from testing.test_cart_management import customer_with_cart_and_token, customer_with_token, setup_restaurant_menu, manager_with_token
from testing.test_restaurant_crud import setup_restaurant

client = TestClient(app)

# places an order
@pytest.fixture
def placed_order(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]

    response = client.post("/order", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201

    return {
        "order": response.json(),
        "token": token,
        "customer_id": customer_with_cart_and_token["customer_id"]
    }

# test successfully cancelling a pending order
def test_cancel_order(placed_order):
    order_id = placed_order["order"]["id"]
    token = placed_order["token"]

    response = client.delete(f"/order/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

# test that cancelled order is removed from the customer's orders list
def test_cancel_order_removed_from_orders(placed_order):
    order_id = placed_order["order"]["id"]
    token = placed_order["token"]

    client.delete(f"/order/{order_id}", headers={"Authorization": f"Bearer {token}"})

    get_response = client.get("/order/customer", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 200
    orders = get_response.json()
    assert not any(order["id"] == order_id for order in orders)

# test cancelling an order that doesn't exist
def test_cancel_nonexistent_order(customer_with_token):
    token = customer_with_token["token"]
    fake_order_id = 999999

    response = client.delete(f"/order/{fake_order_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

# test cancelling someone else's order
def test_cancel_order_wrong_customer(placed_order, setup_restaurant_menu):
    order_id = placed_order["order"]["id"]

    # create a second customer
    other_customer = client.post(
        "/user",
        json={
            "email": "other@example.com",
            "password": "password",
            "name": "Other",
            "age": 25,
            "gender": "male",
            "role": UserRole.CUSTOMER.value
        }
    )
    assert other_customer.status_code == 201

    login_response = client.post(
        "/user/login",
        json={
            "email": "other@example.com",
            "password": "password"
        }
    )
    assert login_response.status_code == 200
    other_token = login_response.json()["token"]

    # try to cancel the first customer's order
    response = client.delete(f"/order/{order_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert response.status_code == 403

# test cancelling an order as a manager (not allowed)
def test_cancel_order_wrong_role(placed_order, manager_with_token):
    order_id = placed_order["order"]["id"]
    manager_token = manager_with_token["token"]

    response = client.delete(f"/order/{order_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 403

# test cancelling an order with no auth token
def test_cancel_order_no_auth(placed_order):
    order_id = placed_order["order"]["id"]

    response = client.delete(f"/order/{order_id}")
    assert response.status_code == 422