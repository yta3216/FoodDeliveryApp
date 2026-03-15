"""Test cases for manager accept/reject order status updates."""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from testing.test_cart_management import (
    customer_with_cart_and_token,
    customer_with_token,
    setup_restaurant_menu,
    manager_with_token,
)
from testing.test_restaurant_crud import setup_restaurant

client = TestClient(app)


@pytest.fixture

# customer creates pending order
def customer_order_with_manager_token(customer_with_cart_and_token, setup_restaurant_menu):
    customer_token = customer_with_cart_and_token["token"]
    manager_token = setup_restaurant_menu["token"]
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

    response = client.post("/order", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 201

    return {
        "order": response.json(),
        "customer_token": customer_token,
        "manager_token": manager_token,
        "restaurant_id": restaurant_id,
    }
# Manager successfully accepts pending order
def test_manager_can_accept_pending_order(customer_order_with_manager_token):
    order_id = customer_order_with_manager_token["order"]["id"]
    manager_token = customer_order_with_manager_token["manager_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

# Manager successfully rejects pending order
def test_manager_can_reject_pending_order(customer_order_with_manager_token):
    order_id = customer_order_with_manager_token["order"]["id"]
    manager_token = customer_order_with_manager_token["manager_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

# manager cannot accept an order which has already been accepted
def test_cannot_accept_already_accepted_order(customer_order_with_manager_token):
    order_id = customer_order_with_manager_token["order"]["id"]
    manager_token = customer_order_with_manager_token["manager_token"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 400

# Customer cannot accept order
def test_customer_cannot_accept_order(customer_order_with_manager_token):
    order_id = customer_order_with_manager_token["order"]["id"]
    customer_token = customer_order_with_manager_token["customer_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403

# test another manager tries update order of another managers orders
def test_manager_of_different_restaurant_cannot_update_order(customer_order_with_manager_token):
    order_id = customer_order_with_manager_token["order"]["id"]

    other_manager = client.post(
        "/user",
        json={
            "email": "other_manager@example.com",
            "password": "password",
            "name": "Other Manager",
            "age": 35,
            "gender": "male",
            "role": UserRole.RESTAURANT_MANAGER.value,
        },
    )
    assert other_manager.status_code == 201

    login = client.post(
        "/user/login",
        json={"email": "other_manager@example.com", "password": "password"},
    )
    assert login.status_code == 200
    other_token = login.json()["token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403

# test updating status of order that DNE
def test_update_status_for_nonexistent_order(setup_restaurant_menu):
    manager_token = setup_restaurant_menu["token"]

    response = client.patch(
        "/order/999999/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 404