"""
tests for orders locked after confirmation uses mocking for order/restaurant data to keep fixtures lean.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)


# fixtures 
@pytest.fixture
def mock_orders(mocker):
    """mocks load_orders and save_orders so tests don't touch the json files."""
    orders = []
    mocker.patch("app.services.order_service.load_orders", side_effect=lambda: list(orders))
    mocker.patch("app.services.order_service.save_orders", side_effect=lambda data: (orders.clear(), orders.extend(data)))
    return orders


@pytest.fixture
def order_setup(mocker, mock_orders):
    """creates real users for auth tokens, then seeds a fake pending order."""

    # create manager
    manager_resp = client.post("/user", json={
        "email": "lock_manager@example.com",
        "password": "password",
        "name": "Lock Manager",
        "age": 30,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    assert manager_resp.status_code == 201
    manager_id = manager_resp.json()["id"]
    manager_token = client.post("/user/login", json={"email": "lock_manager@example.com", "password": "password"}).json()["token"]

    # create customer
    customer_resp = client.post("/user", json={
        "email": "lock_customer@example.com",
        "password": "password",
        "name": "Lock Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    assert customer_resp.status_code == 201
    customer_id = customer_resp.json()["id"]
    customer_token = client.post("/user/login", json={"email": "lock_customer@example.com", "password": "password"}).json()["token"]

    # mock restaurant lookup so manager can accept/reject without a real restaurant
    restaurant_id = 1
    menu_item_id = 1
    mocker.patch("app.services.order_service.get_restaurant_by_id", return_value={
        "id": restaurant_id,
        "manager_ids": [manager_id],
    })

    # seed a fake pending order directly into the mocked orders list
    mock_orders.append({
        "id": 1,
        "customer_id": customer_id,
        "restaurant_id": restaurant_id,
        "delivery_id": 0,
        "items": [{"menu_item_id": menu_item_id, "qty": 2}],
        "status": "pending",
        "delivery_fee": 0.0,
        "tax": 0.0,
        "subtotal": 9.99,
        "date_created": "2026-01-01T00:00:00+00:00",
    })

    return {
        "customer_token": customer_token,
        "manager_token": manager_token,
        "order_id": 1,
        "menu_item_id": menu_item_id,
    }


# tests
# customer can edit items on a pending order
def test_customer_can_edit_pending_order(order_setup):
    order_id = order_setup["order_id"]
    customer_token = order_setup["customer_token"]
    menu_item_id = order_setup["menu_item_id"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 5}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["qty"] == 5


# confirmed order cannot be edited — core lock behaviour
def test_confirmed_order_cannot_be_edited(order_setup):
    order_id = order_setup["order_id"]
    customer_token = order_setup["customer_token"]
    manager_token = order_setup["manager_token"]
    menu_item_id = order_setup["menu_item_id"]

    accept = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert accept.status_code == 200

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 99}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 400


# rejected order also cannot be edited
def test_rejected_order_cannot_be_edited(order_setup):
    order_id = order_setup["order_id"]
    customer_token = order_setup["customer_token"]
    manager_token = order_setup["manager_token"]
    menu_item_id = order_setup["menu_item_id"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "rejected"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 3}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 400


# a different customer cannot edit someone else's order
def test_other_customer_cannot_edit_order(order_setup):
    order_id = order_setup["order_id"]
    menu_item_id = order_setup["menu_item_id"]

    client.post("/user", json={
        "email": "other_lock_customer@example.com",
        "password": "password",
        "name": "Other Customer",
        "age": 30,
        "gender": "male",
        "role": UserRole.CUSTOMER.value,
    })
    other_token = client.post("/user/login", json={"email": "other_lock_customer@example.com", "password": "password"}).json()["token"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


# editing a nonexistent order returns 404
def test_edit_nonexistent_order(order_setup):
    customer_token = order_setup["customer_token"]
    menu_item_id = order_setup["menu_item_id"]

    response = client.patch(
        "/order/999999/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 404


# manager cannot use the items edit route (customers only)
def test_manager_cannot_edit_order_items(order_setup):
    order_id = order_setup["order_id"]
    manager_token = order_setup["manager_token"]
    menu_item_id = order_setup["menu_item_id"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403