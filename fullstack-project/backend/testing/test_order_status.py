"""Test cases for manager accept/reject order status updates."""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from app.routers.websocket_router import connection_manager as cm
from testing.test_cart_management import (
    customer_with_cart_and_token,
    customer_with_token,
    setup_restaurant_menu,
    manager_with_token,
)
from app.services.notification_service import Notification
from app.services.order_service import send_status_notification
from app.schemas.order_schema import Order
from app.schemas.restaurant_schema import Restaurant, Address, Menu
from testing.test_restaurant_crud import setup_restaurant
from testing.test_authorization import register_and_login

client = TestClient(app)

# Helper
def place_order(token: str) -> dict:

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt_id = receipt_response.json()["id"]
 
    client.patch(
        "/payment/topup-wallet",
        json={
            "amount": 100.0,
            "card_number": "1234567890123456",
            "expiry_month": 12,
            "expiry_year": 2099,
            "cvv": "123",
            "cardholder_name": "Test Customer"},
        headers={"Authorization": f"Bearer {token}"}
    )

    checkout_response = client.post(
        "/payment/checkout",
        json={"receipt_id": receipt_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert checkout_response.status_code == 201
    return checkout_response.json()["order"]

@pytest.fixture
# customer creates pending order
def customer_order_with_manager_token(customer_with_cart_and_token, setup_restaurant_menu):
    customer_token = customer_with_cart_and_token["token"]
    manager_token = setup_restaurant_menu["token"]
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

    order = place_order(customer_token)
 
    return {
        "order": order,
        "customer_token": customer_token,
        "manager_token": manager_token,
        "restaurant_id": restaurant_id,
    }

# mock notification
@pytest.fixture
def mock_notif(mocker):
    mock_notif = mocker.patch("app.services.order_service.Notification.send_to_users")
    mock_notif.return_value = None
    return mock_notif

# Manager successfully accepts pending order
def test_manager_can_accept_pending_order(customer_order_with_manager_token, mock_notif):
    order_id = customer_order_with_manager_token["order"]["id"]
    manager_token = customer_order_with_manager_token["manager_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] in ("preparing", "waiting_for_driver", "rejected")

# Manager successfully rejects pending order
def test_manager_can_reject_pending_order(customer_order_with_manager_token, mock_notif):
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
def test_cannot_accept_already_accepted_order(customer_order_with_manager_token, mock_notif):
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
def test_customer_cannot_accept_order(customer_order_with_manager_token, mock_notif):
    order_id = customer_order_with_manager_token["order"]["id"]
    customer_token = customer_order_with_manager_token["customer_token"]

    response = client.patch(
        f"/order/{order_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403

# test another manager tries update order of another managers orders
def test_manager_of_different_restaurant_cannot_update_order(customer_order_with_manager_token, mock_notif):
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
def test_update_status_for_nonexistent_order(setup_restaurant_menu, mock_notif):
    manager_token = setup_restaurant_menu["token"]

    response = client.patch(
        "/order/999999/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert response.status_code == 404

# test sending notification for order status change
@pytest.mark.anyio
async def test_send_status_notification(mocker):
    cm._instance = None
    token, user_id = register_and_login("testuser789@testing.com")
    restaurant_name = "Test Restaurant"
    mock_get_managers = mocker.patch("app.services.order_service.get_managers")
    mock_get_managers.return_value = [user_id] # just send it to the user again for testing purposes
    mock_get_restaurant = mocker.patch("app.services.order_service.get_restaurant_by_id")
    mock_get_restaurant.return_value = Restaurant(
        id=9,
        name=restaurant_name,
        city="Kelowna",
        address=Address(street="123 Main St", city="Kelowna", province="BC", postal_code="A1A 1A1"),
        manager_ids=[user_id],
        menu=Menu(items=[]),
        delivery_fee=5.0,
        max_delivery_radius_km=10.0,
    )
    order = Order(
        id = 5,
        customer_id = user_id,
        restaurant_id = 9,
        status = "pending"
    )
    with client.websocket_connect(
        f"/ws/{user_id}", 
        headers={"Authorization": f"Bearer {token}"}
    ) as websocket:        
        await send_status_notification(order)
        assert websocket.receive_json()["message"] == f"Order {order.id} from {restaurant_name} set to status: {order.status}"