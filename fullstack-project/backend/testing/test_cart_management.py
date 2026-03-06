""" testing cart management """

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole
from app.repositories.user_repo import load_users
from app.services.restaurant_service import get_restaurant_by_id
from testing.test_restaurant_crud import setup_restaurant, VALID_RESTAURANT_ADDRESS

client = TestClient(app)

# --------- FIXTURES --------------#

# create a customer, which has an empty cart by default, to use in tests
@pytest.fixture
def customer_with_token():
    test_customer = client.post(
        "/user",
        json={
            "email": "customer1@example.com",
            "password": "testpassword",
            "name": "Test Customer",
            "age": 19,
            "gender": "female",
            "role": UserRole.CUSTOMER.value
        }
    )
    assert test_customer.status_code == 201

    # log in to get auth token
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

# create a user who is not a customer
@pytest.fixture
def manager_with_token():
    test_manager = client.post(
        "/user",
        json={
            "email": "customer1@example.com",
            "password": "testpassword",
            "name": "Test Customer",
            "age": 19,
            "gender": "female",
            "role": UserRole.RESTAURANT_MANAGER.value
        }
    )
    assert test_manager.status_code == 201

    # log in to get auth token
    login_response = client.post(
        "/user/login",
        json={
            "email": test_manager.json().get("email"),
            "password": "testpassword"
        }
    )
    assert login_response.status_code == 200
    return {
        "customer": test_manager.json,
        "token": login_response.json()["token"]
    }

# create a restaurant with menu to add menu items from
@pytest.fixture
def setup_restaurant_menu(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Create new menu items
    client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Test Menu Item 1",
            "price": 9.99,
            "tags": ["test"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Test Menu Item 2",
            "price": 10.99,
            "tags": ["test"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    return get_restaurant_by_id(restaurant['id'])

# a customer with two items in their cart
@pytest.fixture
def customer_with_cart_and_token(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    item1_id = setup_restaurant_menu["menu"]["items"][0]["id"]
    item2_id = setup_restaurant_menu["menu"]["items"][1]["id"]
    restaurant_id = setup_restaurant_menu["id"]

    # add items to cart
    set_id_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    assert set_id_response.status_code == 200

    client.post(
        "/cart/item",
        json={
            "menu_item_id": item1_id,
            "qty": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/cart/item",
        json={
            "menu_item_id": item2_id,
            "qty": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # get updated customer
    customer = get_customer(customer["id"])

    return {
        "customer": customer,
        "token": token
    }

# get user (for when data is updated)
def get_customer(id: str):
    users = load_users()
    for user in users:
        if user.get("id") == id:
            return user

# --------------- TESTS -------------- #

# test updating cart restaurant id successfully
def test_update_cart_restaurant(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant_menu["id"]

    # send update request
    update_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    # check result
    assert update_response.status_code == 200
    assert update_response.json()["restaurant_id"] == restaurant_id

# test changing restaurant id but user isn't Customer
def test_update_cart_restaurant_wrong_role(manager_with_token, setup_restaurant_menu):
    wrong_role = manager_with_token["customer"]
    token = manager_with_token["token"]
    restaurant_id = setup_restaurant_menu["id"]

    # send update request
    update_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    # check result
    assert update_response.status_code == 403

# test changing restaurant id but restaurant id doesn't exist
def test_update_cart_wrong_restaurant(customer_with_token):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    nonexistent_id = 123456

    # send update request
    update_response = client.put(
        f"/cart/{nonexistent_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    # check result
    assert update_response.status_code == 404


# test emptying cart with an item in it
def test_emptying_cart(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    update_response = client.delete("/cart", headers={"Authorization": f"Bearer {token}"})
    updated_customer = get_customer(customer["id"])

    assert update_response.status_code == 204
    assert len(updated_customer["cart"]["cart_items"]) == 0

# test emptying cart when it has nothing in it
def test_emptying_empty_cart(customer_with_token):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]

    update_response = client.delete("/cart", headers={"Authorization": f"Bearer {token}"})
    updated_customer = get_customer(customer["id"])

    assert update_response.status_code == 204
    assert len(updated_customer["cart"]["cart_items"]) == 0

# test emptying cart when user is not Customer
def test_emptying_cart_wrong_role(manager_with_token):
    customer = manager_with_token["customer"]
    token = manager_with_token["token"]

    update_response = client.delete("/cart", headers={"Authorization": f"Bearer {token}"})
    assert update_response.status_code == 403

# test adding new item to cart successfully
def test_add_item_to_cart(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    item1_id = setup_restaurant_menu["menu"]["items"][0]["id"]
    item2_id = setup_restaurant_menu["menu"]["items"][1]["id"]
    restaurant_id = setup_restaurant_menu["id"]

    # add items to cart
    set_id_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    assert set_id_response.status_code == 200

    update1_response = client.post(
        "/cart/item",
        json={
            "menu_item_id": item1_id,
            "qty": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update1_response.status_code == 201
    assert update1_response.json()["menu_item_id"] == 1

    update2_response = client.post(
        "/cart/item",
        json={
            "menu_item_id": item2_id,
            "qty": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update1_response.status_code == 201
    assert update1_response.json()["menu_item_id"] == item1_id

    # get updated customer, check cart size
    customer = get_customer(customer["id"])
    assert len(customer["cart"]["cart_items"]) == item2_id

# test adding items but item id doesn't exist in menu (need to check)

# UPDATE QTY of item
# test successful
# item id not found in users cart

# DELETE item from cart
# successful
# item id not found
