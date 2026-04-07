"""Test cases for receipt generation and refreshing."""

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.user_schema import UserRole
from testing.test_cart_management import customer_with_cart_and_token, customer_with_token
from testing.test_restaurant_crud import setup_restaurant, setup_restaurant_menu
from testing.test_payment_simulation import VALID_PAYMENT, get_orders_for_customer, get_receipt_id
from testing.test_tax_rate_management import admin_token

client = TestClient(app)

def test_generate_receipt(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    restaurant = customer_with_cart_and_token["restaurant_id"]

    response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    receipt = response.json()
    assert receipt["customer_id"] == customer_with_cart_and_token["customer_id"]
    assert receipt["restaurant_id"] == restaurant
    assert isinstance(receipt["items"], list)
    assert len(receipt["items"]) == 2

def test_receipt_subtotal_matches_cart(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    restaurant_items = setup_restaurant_menu["restaurant"]["menu"]["items"]

    subtotal = round((restaurant_items[0]["price"] * 2) + (restaurant_items[1]["price"] * 1), 2)

    response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    receipt = response.json()

    assert round(receipt["subtotal"], 2) == subtotal


def test_receipt_applies_combo_discount(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]
    manager_token = setup_restaurant_menu["token"]
    item_one = restaurant["menu"]["items"][0]["id"]
    item_two = restaurant["menu"]["items"][1]["id"]

    combo_response = client.post(
        f"/restaurant/{restaurant['id']}/menu/combo",
        json={
            "name": "Receipt Combo",
            "discount": 2.00,
            "type": "fixed_amount",
            "item_ids": [item_one, item_two],
            "is_active": True,
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert combo_response.status_code == 201
    assert combo_response.json()["is_active"] is True

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt = receipt_response.json()

    assert receipt["discount"] == 2.0
    assert receipt["total"] == round(receipt["subtotal"] + receipt["tax"] + receipt["delivery_fee"] - 2.0, 2)

def test_receipt_ignores_inactive_combo(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]
    manager_token = setup_restaurant_menu["token"]
    item_one = restaurant["menu"]["items"][0]["id"]
    item_two = restaurant["menu"]["items"][1]["id"]

    combo_response = client.post(
        f"/restaurant/{restaurant['id']}/menu/combo",
        json={
            "name": "Inactive Combo",
            "discount": 5.00,
            "type": "fixed_amount",
            "item_ids": [item_one, item_two],
            "is_active": False,
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert combo_response.status_code == 201
    assert combo_response.json()["is_active"] is False

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt = receipt_response.json()

    assert receipt["discount"] == 0.0
    assert receipt["total"] == round(receipt["subtotal"] + receipt["tax"] + receipt["delivery_fee"], 2)

def test_receipt_different_delivery_fee_refresh(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer_id"]
    restaurant = setup_restaurant_menu["restaurant"]
    manager = setup_restaurant_menu["token"]

    receipt = get_receipt_id(token)

    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": restaurant["name"],
            "city": restaurant["city"],
            "address": restaurant["address"],
            "delivery_fee": 6.76
        },
        headers={"Authorization": f"Bearer {manager}"}
    )
    assert response.status_code == 200

    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {token}"}
    )

    response_checkout = client.post(
        "/payment/checkout",
        json={"receipt_id": receipt},
        headers={"Authorization": f"Bearer {token}"}
    )

    order_len = len(get_orders_for_customer(customer_id))

    assert response_checkout.status_code == 409
    assert len(get_orders_for_customer(customer_id)) == order_len

    receipt_new = get_receipt_id(token)
    assert receipt_new != receipt

    response_checkout_2 = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_new},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response_checkout_2.status_code == 201

def test_receipt_different_tax_rate_refresh(customer_with_cart_and_token, admin_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer_id"]

    receipt = get_receipt_id(token)

    response = client.patch("/config/tax-rate?new_tax_rate=0.15", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    client.patch(
        "/payment/topup-wallet",
        json={**VALID_PAYMENT},
        headers={"Authorization": f"Bearer {token}"}
    )

    response_checkout = client.post(
        "/payment/checkout",
        json={"receipt_id": receipt},
        headers={"Authorization": f"Bearer {token}"}
    )

    order_len = len(get_orders_for_customer(customer_id))

    assert response_checkout.status_code == 409
    assert len(get_orders_for_customer(customer_id)) == order_len

    receipt_new = get_receipt_id(token)
    assert receipt_new != receipt

    response_checkout_2 = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_new},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response_checkout_2.status_code == 201