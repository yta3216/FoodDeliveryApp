""" testing cart management """

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole, Customer
from app.repositories.user_repo import load_users
from app.services.restaurant_service import get_restaurant_by_id
from testing.test_restaurant_crud import setup_restaurant, VALID_RESTAURANT_ADDRESS

client = TestClient(app)

# --------- FIXTURES & HELPER FUNCTIONS --------------#

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
            "email": "manager1@example.com",
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
    return {
        "restaurant": get_restaurant_by_id(restaurant['id']),
        "token": token
    }

# a customer with two items in their cart
@pytest.fixture
def customer_with_cart_and_token(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    item1_id = setup_restaurant_menu["restaurant"]["menu"]["items"][0]["id"]
    item2_id = setup_restaurant_menu["restaurant"]["menu"]["items"][1]["id"]
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

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
        "token": token,
        "restaurant_id": restaurant_id,
        "customer_id": customer["id"]
    }

# get user (for when data is updated)
def get_customer(id: str):
    users = load_users()
    for user in users:
        if user.get("id") == id:
            return user
        
# get a fake menu item id which is definitely not in users cart
def get_fake_cart_item_id(customer: Customer):
    # get max id so we can set a fake id as larger than it
    max = 0
    for cart_item in customer["cart"]["cart_items"]:
        if cart_item["menu_item_id"] > max:
            max = cart_item["menu_item_id"]
    return max + 5

# --------------- TESTS -------------- #

# test getting cart successfully
def test_get_cart(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    # send get request
    get_response = client.get("/cart", headers={"Authorization": f"Bearer {token}"})
    # check response
    assert get_response.status_code == 200
    assert get_response.json() == customer["cart"]

# test getting cart but user is not customer
def test_get_cart_wrong_role(manager_with_token):
    token = manager_with_token["token"]
    # send update request
    get_response = client.get("/cart", headers={"Authorization": f"Bearer {token}"})
    # check result
    assert get_response.status_code == 403

# test getting cart item
def test_get_cart_item(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]
    cart_item = customer["cart"]["cart_items"][0]
    cart_item_id = cart_item["menu_item_id"]

    # send get request
    get_response = client.get(
        f"/cart/item/{cart_item_id}", 
        headers={"Authorization": f"Bearer {token}"}
    )
    # check response
    assert get_response.status_code == 200
    assert get_response.json() == cart_item

# test getting cart item which doesn't exist
def test_get_cart_item_wrong_id(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]
    # get an invalid cart item id
    wrong_item_id = get_fake_cart_item_id(customer)
    # get the response, assert that 404 status is returned
    get_response = client.get(
        f"/cart/item/{wrong_item_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404

# test updating cart restaurant id successfully
def test_update_cart_restaurant(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

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
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

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
    item1_id = setup_restaurant_menu["restaurant"]["menu"]["items"][0]["id"]
    item2_id = setup_restaurant_menu["restaurant"]["menu"]["items"][1]["id"]
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

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
    assert update2_response.status_code == 201
    assert update2_response.json()["menu_item_id"] == item2_id

    # get updated customer, check cart size
    customer = get_customer(customer["id"])
    assert len(customer["cart"]["cart_items"]) == item2_id

# test adding items but item id doesn't exist in menu
# test adding new item to cart successfully
def test_add_nonexistent_item(customer_with_token, setup_restaurant_menu):
    customer = customer_with_token["customer"]
    token = customer_with_token["token"]
    max_id = 5*len(setup_restaurant_menu["restaurant"]["menu"]["items"]) # five times larger than size of menu
    restaurant_id = setup_restaurant_menu["restaurant"]["id"]

    # add item to cart who is not in restaurant menu
    set_id_response = client.put(
        f"/cart/{restaurant_id}",
        headers={"Authorization": f"Bearer {token}"}
        )
    assert set_id_response.status_code == 200

    update1_response = client.post(
        "/cart/item",
        json={
            "menu_item_id": max_id,
            "qty": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update1_response.status_code == 404

# test update qty of item in cart successfully
def test_successful_qty_change(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    item_id = customer["cart"]["cart_items"][0]["menu_item_id"]

    update_response = client.put(
        f"/cart/item/{item_id}",
        json={
            "new_qty": 5
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert update_response.status_code == 200
    assert update_response.json()["qty"] == 5

# test update qty if item id not found in users cart
def test_qty_change_wrong_item(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    wrong_item_id = get_fake_cart_item_id(customer)

    update_response = client.put(
        f"/cart/item/{wrong_item_id}",
        json={
            "new_qty": 7
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert update_response.status_code == 404

# test successful item deletion from cart
def def_cart_item_removal(customer_with_cart_and_token):
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    # get item id to remove
    item_id = customer["cart"]["cart_items"][0]["menu_item_id"]

    # remove it
    update_response = client.delete("cart/item/{item_id}", headers={"Authorization": f"Bearer {token}"})
    assert update_response.status_code == 404
    
# test item deletion attempt but item id not found
    customer = customer_with_cart_and_token["customer"]
    token = customer_with_cart_and_token["token"]

    wrong_item_id = get_fake_cart_item_id(customer)

    update_response = client.put(
        f"/cart/item/{wrong_item_id}",
        json={
            "new_qty": 7
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert update_response.status_code == 404
    