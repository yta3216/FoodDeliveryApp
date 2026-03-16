from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from app.repositories.user_repo import load_users
from app.repositories.order_repo import load_orders
from app.services.restaurant_service import get_restaurant_by_id
from testing.test_restaurant_crud import setup_restaurant, VALID_RESTAURANT_ADDRESS

client = TestClient(app)

# valid payment details to reuse across tests
VALID_PAYMENT = {
    "card_number": "1234567890123456",
    "expiry_month": 12,
    "expiry_year": 2099,
    "cvv": "123",
    "cardholder_name": "Test Customer"
}

# create a customer
@pytest.fixture
def customer_with_token():
    test_customer = client.post(
        "/user",
        json={
            "email": "customer_pay@example.com",
            "password": "testpassword",
            "name": "John Kwon",
            "age": 25,
            "gender": "male",
            "role": UserRole.CUSTOMER.value
        }
    )
    assert test_customer.status_code == 201

    login_response = client.post(
        "/user/login",
        json={
            "email": test_customer.json().get("email"),
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200
    return {
        "customer": test_customer.json(),
        "token": login_response.json()["token"]
    }
# create a manager
@pytest.fixture
def manager_with_token():
    test_manager = client.post(
        "/user",
        json={
            "email": "manager_pay@example.com",
            "password": "testpassword",
            "name": "Kwon John",
            "age": 30,
            "gender": "male",
            "role": UserRole.RESTAURANT_MANAGER.value
        }
    )
    assert test_manager.status_code == 201
 
    login_response = client.post(
        "/user/login",
        json={
            "email": test_manager.json().get("email"),
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200
    return {
        "manager": test_manager.json(),
        "token": login_response.json()["token"]
    }

# create a restaurant with two menu items
@pytest.fixture
def setup_restaurant_menu(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "California roll", "price": 9.99, "tags": ["sushi"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Salmon roll", "price": 10.99, "tags": ["sushi"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    return {
        "restaurant": get_restaurant_by_id(restaurant["id"]),
        "token": token
    }

# a customer with a filled cart, ready to check out
@pytest.fixture
def customer_with_cart_and_token(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]
    restaurant_id = restaurant["id"]
    item1_id = restaurant["menu"]["items"][0]["id"]
    item2_id = restaurant["menu"]["items"][1]["id"]

    # set cart restaurant
    set_restaurant_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert set_restaurant_response.status_code == 200

    # add items
    client.post(
        "/cart/item",
        json={"menu_item_id": item1_id, "qty": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/cart/item",
        json={"menu_item_id": item2_id, "qty": 1},
        headers={"Authorization": f"Bearer {token}"}
    )

    return {
        "customer": customer,
        "token": token,
        "restaurant_id": restaurant_id
    }

def get_customer_from_db(customer_id: str):
    users = load_users()
    for user in users:
        if user.get("id") == customer_id:
            return user

def get_orders_for_customer(customer_id: str):
    orders = load_orders()
    return [o for o in orders if o.get("customer_id") == customer_id]

def get_receipt_id(token: str) -> int:
    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    return receipt_response.json()["id"]

# test successful checkout: valid payment with an item in cart
def test_successful_checkout(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    assert response.json()["payment_status"] == "success"
    assert response.json()["order"] is not None
    assert response.json()["order"]["status"] == "pending"
    assert response.json()["order"]["customer_id"] == customer_id


# test that a successful payment creates exactly one order in storage
def test_successful_checkout_creates_order(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    orders_before = get_orders_for_customer(customer_id)

    client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    orders_after = get_orders_for_customer(customer_id)
    assert len(orders_after) == len(orders_before) + 1

# test that a successful payment empties the cart
def test_successful_checkout_empties_cart(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id},
        headers={"Authorization": f"Bearer {token}"}
    )

    updated_customer = get_customer_from_db(customer_id)
    assert len(updated_customer["cart"]["cart_items"]) == 0

# test that order subtotal matches expected cart total
def test_successful_checkout_correct_subtotal(customer_with_cart_and_token, setup_restaurant_menu):
    token = customer_with_cart_and_token["token"]
    restaurant = setup_restaurant_menu["restaurant"]

    item1_price = restaurant["menu"]["items"][0]["price"]
    item2_price = restaurant["menu"]["items"][1]["price"]
    expected_subtotal = round((item1_price * 2) + (item2_price * 1), 2)

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 200
    receipt = receipt_response.json()
    assert round(receipt["subtotal"], 2) == expected_subtotal

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt["id"]},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201

# test that checkout fails when cart is empty
def test_checkout_with_empty_cart(customer_with_token):
    token = customer_with_token["token"]
    customer_id = customer_with_token["customer"]["id"]

    receipt_response = client.get("/receipt", headers={"Authorization": f"Bearer {token}"})
    assert receipt_response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with card number shorter than 16 digits
def test_checkout_short_card_number(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "card_number": "12345"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with card number longer than 16 digits
def test_checkout_long_card_number(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "card_number": "12345678901234567"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with non-digit characters in card number
def test_checkout_non_digit_card_number(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "card_number": "1234abcd56789012"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with hardcoded declined card
def test_checkout_declined_card(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "card_number": "0000000000000000"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with expired card
def test_checkout_expired_card(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "expiry_month": 1, "expiry_year": 2020},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with invalid expiry month
def test_checkout_invalid_expiry_month(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "expiry_month": 13},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with invalid CVV (too short)
def test_checkout_invalid_cvv(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "cvv": "12"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test payment fails with empty cardholder name
def test_checkout_empty_cardholder_name(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    response = client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "cardholder_name": "   "},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert len(get_orders_for_customer(customer_id)) == 0

# test that a failed payment leaves the cart untouched
def test_failed_payment_cart_preserved(customer_with_cart_and_token):
    token = customer_with_cart_and_token["token"]
    customer_id = customer_with_cart_and_token["customer"]["id"]
    receipt_id = get_receipt_id(token)

    cart_before = get_customer_from_db(customer_id)["cart"]

    client.post(
        "/payment/checkout",
        json={**VALID_PAYMENT, "receipt_id": receipt_id, "card_number": "0000000000000000"},
        headers={"Authorization": f"Bearer {token}"}
    )

    cart_after = get_customer_from_db(customer_id)["cart"]
    assert cart_after == cart_before