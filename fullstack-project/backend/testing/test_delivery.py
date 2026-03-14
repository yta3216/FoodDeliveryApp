import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)


# fixtures
@pytest.fixture
def delivery_setup():

    # create manager
    client.post("/user", json={
        "email": "delivery_manager@example.com",
        "password": "password",
        "name": "Delivery Manager",
        "age": 35,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    manager_token = client.post("/user/login", json={
        "email": "delivery_manager@example.com", "password": "password"
    }).json()["token"]

    # create restaurant
    restaurant_resp = client.post("/restaurant", json={
        "name": "Delivery Test Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "123 Delivery St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B1A1"
        }
    }, headers={"Authorization": f"Bearer {manager_token}"})
    assert restaurant_resp.status_code == 201
    restaurant_id = restaurant_resp.json()["id"]

    # create menu item
    menu_resp = client.post(f"/restaurant/{restaurant_id}/menu", json={
        "name": "Delivery Burger",
        "price": 9.99,
        "tags": ["test"]
    }, headers={"Authorization": f"Bearer {manager_token}"})
    assert menu_resp.status_code == 201
    menu_item_id = menu_resp.json()["id"]

    # create customer
    client.post("/user", json={
        "email": "delivery_customer@example.com",
        "password": "password",
        "name": "Delivery Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    customer_token = client.post("/user/login", json={
        "email": "delivery_customer@example.com", "password": "password"
    }).json()["token"]

    # create bike driver
    client.post("/user", json={
        "email": "delivery_driver@example.com",
        "password": "password",
        "name": "Delivery Driver",
        "age": 28,
        "gender": "male",
        "role": UserRole.DELIVERY_DRIVER.value,
        "vehicle": "bike",
    })
    driver_token = client.post("/user/login", json={
        "email": "delivery_driver@example.com", "password": "password"
    }).json()["token"]

    # set driver to available
    client.patch(
        "/delivery/status?status=available",
        headers={"Authorization": f"Bearer {driver_token}"}
    )

    # add item to cart and place order with 3km distance (bike range)
    client.put(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order_resp = client.post("/order",
                             json={"distance_km": 3.0},
                             headers={"Authorization": f"Bearer {customer_token}"})
    assert order_resp.status_code == 201

    return {
        "manager_token": manager_token,
        "customer_token": customer_token,
        "driver_token": driver_token,
        "order": order_resp.json(),
        "restaurant_id": restaurant_id,
    }

# when manager accepts and a bike driver is available, order goes to delivering
def test_manager_accept_assigns_driver(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "delivering"


# when no driver is available, order goes to waiting_for_driver
def test_no_driver_sets_waiting_status():
    # create manager, restaurant, customer, order with no driver registered
    client.post("/user", json={
        "email": "nodriver_manager@example.com",
        "password": "password",
        "name": "No Driver Manager",
        "age": 35,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    manager_token = client.post("/user/login", json={
        "email": "nodriver_manager@example.com", "password": "password"
    }).json()["token"]

    restaurant_resp = client.post("/restaurant", json={
        "name": "No Driver Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "456 No Driver St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B2B2"
        }
    }, headers={"Authorization": f"Bearer {manager_token}"})
    restaurant_id = restaurant_resp.json()["id"]

    menu_resp = client.post(f"/restaurant/{restaurant_id}/menu", json={
        "name": "Burger",
        "price": 9.99,
        "tags": ["test"]
    }, headers={"Authorization": f"Bearer {manager_token}"})
    menu_item_id = menu_resp.json()["id"]

    client.post("/user", json={
        "email": "nodriver_customer@example.com",
        "password": "password",
        "name": "No Driver Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    customer_token = client.post("/user/login", json={
        "email": "nodriver_customer@example.com", "password": "password"
    }).json()["token"]

    client.put(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order_resp = client.post("/order",
                             json={"distance_km": 3.0},
                             headers={"Authorization": f"Bearer {customer_token}"})
    order_id = order_resp.json()["id"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "waiting_for_driver"


# distance <=5km assigns bike, >5km assigns car
def test_bike_assigned_for_short_distance(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]
    customer_token = delivery_setup["customer_token"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    delivery_resp = client.get(
        f"/delivery/{order_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert delivery_resp.status_code == 200
    assert delivery_resp.json()["method"] == "bike"


# driver can start delivery and eta is calculated
def test_driver_can_start_delivery(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]
    driver_token = delivery_setup["driver_token"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    response = client.patch(
        f"/delivery/{order_id}/start",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert response.status_code == 200
    assert response.json()["eta_minutes"] > 0
    assert response.json()["started_at"] > 0


# driver can complete delivery and actual time is recorded
def test_driver_can_complete_delivery(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]
    driver_token = delivery_setup["driver_token"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    client.patch(
        f"/delivery/{order_id}/start",
        headers={"Authorization": f"Bearer {driver_token}"},
    )

    response = client.patch(
        f"/delivery/{order_id}/complete",
        headers={"Authorization": f"Bearer {driver_token}"},
    )
    assert response.status_code == 200
    assert response.json()["delivered_at"] > 0
    assert response.json()["actual_minutes"] >= 0


# customer can view delivery info for their order
def test_customer_can_view_delivery(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]
    customer_token = delivery_setup["customer_token"]

    client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    response = client.get(
        f"/delivery/{order_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 200
    assert response.json()["order_id"] == order_id