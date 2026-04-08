import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)

VALID_PAYMENT = {
    "amount": 100.0,
    "card_number": "1234567890123456",
    "expiry_month": 12,
    "expiry_year": 2099,
    "cvv": "123",
    "cardholder_name": "Test Customer"
}

# helper to place an order via the payment flow
def place_order(customer_token: str, distance_km: float = 0.0) -> dict:
    receipt_resp = client.get(f"/receipt?distance_km={distance_km}", headers={"Authorization": f"Bearer {customer_token}"})
    assert receipt_resp.status_code == 200
    receipt_id = receipt_resp.json()["id"]
    checkout_resp = client.post(
        "/payment/checkout",
        json={"receipt_id": receipt_id},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert checkout_resp.status_code == 201
    return checkout_resp.json()["order"]


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
    # add money to wallet
    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

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
    client.patch(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order = place_order(customer_token, distance_km=3.0)

    return {
        "manager_token": manager_token,
        "customer_token": customer_token,
        "driver_token": driver_token,
        "order": order,
        "restaurant_id": restaurant_id,
    }


# when manager accepts and a bike driver is available, order goes to preparing
def test_manager_accept_assigns_driver(delivery_setup):
    order_id = delivery_setup["order"]["id"]
    manager_token = delivery_setup["manager_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "preparing"


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
    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    client.patch(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order = place_order(customer_token)
    order_id = order["id"]

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
@pytest.mark.anyio
async def test_driver_can_start_delivery(delivery_setup):
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
    customer_token = delivery_setup["customer_token"]
    order_resp = client.get("/order/customer", headers={"Authorization": f"Bearer {customer_token}"})
    orders = [o for o in order_resp.json() if o["id"] == order_id]
    assert orders[0]["status"] == "delivering"


# driver can complete delivery and actual time is recorded
@pytest.mark.anyio
async def test_driver_can_complete_delivery(delivery_setup):
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
    assert "delay_minutes" in response.json()


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


# when a driver becomes available, waiting_for_driver order gets assigned to them
def test_waiting_order_assigned_when_driver_becomes_available():
    # create manager, restaurant, customer with no driver initially
    client.post("/user", json={
        "email": "wait_manager@example.com",
        "password": "password",
        "name": "Wait Manager",
        "age": 35,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    manager_token = client.post("/user/login", json={
        "email": "wait_manager@example.com", "password": "password"
    }).json()["token"]

    restaurant_resp = client.post("/restaurant", json={
        "name": "Wait Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "789 Wait St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B3C3"
        }
    }, headers={"Authorization": f"Bearer {manager_token}"})
    restaurant_id = restaurant_resp.json()["id"]

    menu_resp = client.post(f"/restaurant/{restaurant_id}/menu", json={
        "name": "Wait Burger",
        "price": 9.99,
        "tags": ["test"]
    }, headers={"Authorization": f"Bearer {manager_token}"})
    menu_item_id = menu_resp.json()["id"]

    client.post("/user", json={
        "email": "wait_customer@example.com",
        "password": "password",
        "name": "Wait Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    customer_token = client.post("/user/login", json={
        "email": "wait_customer@example.com", "password": "password"
    }).json()["token"]
    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # place order with no driver available - should go to waiting_for_driver
    client.patch(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order = place_order(customer_token)
    order_id = order["id"]

    accept = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert accept.json()["status"] == "waiting_for_driver"

    # now a bike driver registers and sets themselves available
    client.post("/user", json={
        "email": "wait_driver@example.com",
        "password": "password",
        "name": "Wait Driver",
        "age": 28,
        "gender": "male",
        "role": UserRole.DELIVERY_DRIVER.value,
        "vehicle": "bike",
    })
    driver_token = client.post("/user/login", json={
        "email": "wait_driver@example.com", "password": "password"
    }).json()["token"]

    client.patch(
        "/delivery/status?status=available",
        headers={"Authorization": f"Bearer {driver_token}"}
    )

    # order should now be assigned to the driver and status should be preparing
    order_check = client.get("/order/customer", headers={"Authorization": f"Bearer {customer_token}"})
    orders = [o for o in order_check.json() if o["id"] == order_id]
    assert orders[0]["status"] == "preparing"

# order outside restaurant's delivery radius gets auto-declined when manager accepts
def test_order_outside_delivery_radius_auto_declined():
    client.post("/user", json={
        "email": "radius_manager@example.com",
        "password": "password",
        "name": "Radius Manager",
        "age": 35,
        "gender": "male",
        "role": UserRole.RESTAURANT_MANAGER.value,
    })
    manager_token = client.post("/user/login", json={
        "email": "radius_manager@example.com", "password": "password"
    }).json()["token"]

    # create restaurant with 5km delivery radius
    restaurant_resp = client.post("/restaurant", json={
        "name": "Radius Restaurant",
        "city": "Vancouver",
        "address": {
            "street": "101 Radius St",
            "city": "Vancouver",
            "province": "BC",
            "postal_code": "V6B4D4"
        },
        "max_delivery_radius_km": 5.0
    }, headers={"Authorization": f"Bearer {manager_token}"})
    restaurant_id = restaurant_resp.json()["id"]

    menu_resp = client.post(f"/restaurant/{restaurant_id}/menu", json={
        "name": "Radius Burger",
        "price": 9.99,
        "tags": ["test"]
    }, headers={"Authorization": f"Bearer {manager_token}"})
    menu_item_id = menu_resp.json()["id"]

    client.post("/user", json={
        "email": "radius_customer@example.com",
        "password": "password",
        "name": "Radius Customer",
        "age": 25,
        "gender": "female",
        "role": UserRole.CUSTOMER.value,
    })
    customer_token = client.post("/user/login", json={
        "email": "radius_customer@example.com", "password": "password"
    }).json()["token"]
    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {customer_token}"}
    )

    # place order with 10km distance - outside the 5km radius
    client.patch(f"/cart/{restaurant_id}", headers={"Authorization": f"Bearer {customer_token}"})
    client.post("/cart/item", json={"menu_item_id": menu_item_id, "qty": 1},
                headers={"Authorization": f"Bearer {customer_token}"})
    order = place_order(customer_token, distance_km=10.0)
    order_id = order["id"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"