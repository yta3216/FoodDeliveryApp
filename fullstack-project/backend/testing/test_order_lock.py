""" tests for orders locked after confirmation. """

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)


# fixtures
@pytest.fixture
def customer_with_order():
    """creates a manager, restaurant, menu item, customer, cart, and order all in one."""

    # create manager and log in
    client.post("/user", json={
        "email": "lock_manager@example.com",
        "password": "password",
        "name": "Lock Manager",
        "age": 30,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    manager_login = client.post("/user/login", json={"email": "lock_manager@example.com", "password": "password"})
    manager_token = manager_login.json()["token"]

    # create restaurant
    restaurant_resp = client.post("/restaurant", json={
        "name": "Lock Test Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "123 Lock St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B1A1"
        }
    }, headers={"Authorization": f"Bearer {manager_token}"})
    assert restaurant_resp.status_code == 201
    restaurant_id = restaurant_resp.json()["id"]

    # create a menu item
    menu_resp = client.post(f"/restaurant/{restaurant_id}/menu", json={
        "name": "Lock Burger",
        "price": 9.99,
        "tags": ["test"]
    }, headers={"Authorization": f"Bearer {manager_token}"})
    assert menu_resp.status_code == 201
    menu_item_id = menu_resp.json()["id"]

    # create customer and log in
    client.post("/user", json={
        "email": "lock_customer@example.com",
        "password": "password",
        "name": "Lock Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    customer_login = client.post("/user/login", json={"email": "lock_customer@example.com", "password": "password"})
    customer_token = customer_login.json()["token"]

    # set cart restaurant and add item
    client.put(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 2}, headers={"Authorization": f"Bearer {customer_token}"})

    # place order
    order_resp = client.post("/order", headers={"Authorization": f"Bearer {customer_token}"})
    assert order_resp.status_code == 201

    return {
        "customer_token": customer_token,
        "manager_token": manager_token,
        "order": order_resp.json(),
        "menu_item_id": menu_item_id,
    }


# tests
# customer can edit items on a pending order
def test_customer_can_edit_pending_order(customer_with_order):
    order_id = customer_with_order["order"]["id"]
    customer_token = customer_with_order["customer_token"]
    menu_item_id = customer_with_order["menu_item_id"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 5}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["qty"] == 5


# confirmed order cannot be edited — core lock behaviour
def test_confirmed_order_cannot_be_edited(customer_with_order):
    order_id = customer_with_order["order"]["id"]
    customer_token = customer_with_order["customer_token"]
    manager_token = customer_with_order["manager_token"]
    menu_item_id = customer_with_order["menu_item_id"]

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
def test_rejected_order_cannot_be_edited(customer_with_order):
    order_id = customer_with_order["order"]["id"]
    customer_token = customer_with_order["customer_token"]
    manager_token = customer_with_order["manager_token"]
    menu_item_id = customer_with_order["menu_item_id"]

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
def test_other_customer_cannot_edit_order(customer_with_order):
    order_id = customer_with_order["order"]["id"]
    menu_item_id = customer_with_order["menu_item_id"]

    client.post("/user", json={
        "email": "other_lock_customer@example.com",
        "password": "password",
        "name": "Other Customer",
        "age": 30,
        "gender": "male",
        "role": UserRole.CUSTOMER.value,
    })
    login = client.post("/user/login", json={"email": "other_lock_customer@example.com", "password": "password"})
    other_token = login.json()["token"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


# editing a nonexistent order returns 404
def test_edit_nonexistent_order(customer_with_order):
    customer_token = customer_with_order["customer_token"]
    menu_item_id = customer_with_order["menu_item_id"]

    response = client.patch(
        "/order/999999/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 404


# manager cannot use the items edit route (customers only)
def test_manager_cannot_edit_order_items(customer_with_order):
    order_id = customer_with_order["order"]["id"]
    manager_token = customer_with_order["manager_token"]
    menu_item_id = customer_with_order["menu_item_id"]

    response = client.patch(
        f"/order/{order_id}/items",
        json={"items": [{"menu_item_id": menu_item_id, "qty": 1}]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 403