""" testing restaurant creation."""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)

VALID_RESTAURANT_ADDRESS = {
    "street": "123 Main St",
    "city": "Kelowna",
    "province": "BC",
    "postal_code": "A1A 1A1"
}

@pytest.fixture
def setup_restaurant():
    # Create a test user with manager role

    test_manager = client.post(
        "/user",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "name": "Test Manager",
            "age": 30,
            "gender": "female",
            "role": "manager",
        }
    )
    assert test_manager.status_code == 201
    
    # Log in as the manager to get an auth token
    login_response = client.post(
        "/user/login",
        json={
            "email": test_manager.json().get("email"),
            "password": "testpassword",
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Now create a restaurant using the manager's token
    restaurant_response = client.post(
        "/restaurant",
        json={
            "name": "Test Restaurant",
            "city": "Test City",
            "address": VALID_RESTAURANT_ADDRESS
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restaurant_response.status_code == 201

    return {
        "restaurant": restaurant_response.json(),
        "token": token
    }

# test a standard restaurant creation process
def test_create_restaurant(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    assert restaurant["name"] == "Test Restaurant"
    assert restaurant["menu"]['items'] == []  # Restaurant should have an associated menu, which starts empty
    assert restaurant["address"]["street"] == "123 Main St"
    assert restaurant["address"]["city"] == "Kelowna"
    assert restaurant["address"]["province"] == "BC"
    assert restaurant["address"]["postal_code"] == "A1A 1A1"

# test a typical restaurant update
def test_update_restaurant_details(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Update the restaurant details
    update_response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": "Updated Restaurant",
            "city": "Updated City",
            "address": {
                "street": "456 Updated St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "B1B 1B1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    updated_restaurant = update_response.json()
    assert updated_restaurant["name"] == "Updated Restaurant"

# test updating restaurant managers
def test_update_restaurant_managers(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # create a second manager to add to the restaurant
    
    second_manager = client.post(
        "/user",
        json={
            "email": "secondmanager@example.com",
            "password": "testpassword",
            "name": "Second Manager",
            "age": 35,
            "gender": "male",
            "role": UserRole.RESTAURANT_MANAGER,
        }
    )

    second_manager_id = second_manager.json().get("id")

    # Update the restaurant managers
    update_response = client.put(
        f"/restaurant/{restaurant['id']}/managers",
        json={
            "id": restaurant["id"],
            "manager_ids": [restaurant["manager_ids"][0], second_manager_id]  # Re-assign the same manager and add the new manager
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    updated_restaurant = update_response.json()
    assert updated_restaurant["manager_ids"] == [restaurant["manager_ids"][0], second_manager_id]

# test updating restaurant with a manager who is not in the manager list
def test_manager_not_in_list(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # create a second manager, but not in the manager list
    
    unauthorized_manager = client.post(
        "/user",
        json={
            "email": "unauthorizedmanager@example.com",
            "password": "testpassword",
            "name": "Unauthorized Manager",
            "age": 52,
            "gender": "male",
            "role": UserRole.RESTAURANT_MANAGER,
        }
    )

    # Log in as the manager to get an auth token
    login_response = client.post(
        "/user/login",
        json={
            "email": unauthorized_manager.json().get("email"),
            "password": "testpassword",
        }
    )
    assert login_response.status_code == 200
    other_token = login_response.json()["token"]

    # Attempt to update restaurant details
    update_response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": "Updated Restaurant",
            "city": "Updated City",
            "address": {
                "street": "789 Updated St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "B1B 1B1"
            }
        },
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert update_response.status_code == 403

# ------- MENU OPERATIONS ------- #

# test creating menu item
def test_create_menu_item(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Create a new menu item
    menu_item_response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Test Menu Item",
            "price": 9.99,
            "tags": ["test"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert menu_item_response.status_code == 201
    menu_item = menu_item_response.json()
    assert menu_item["name"] == "Test Menu Item"
    assert menu_item["price"] == 9.99
    assert menu_item["tags"] == ["test"]

# test updating a menu item
def test_update_menu_item(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Create a menu item to update
    menu_item_response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Original Menu Item",
            "price": 5.99,
            "tags": ["test", "original"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert menu_item_response.status_code == 201
    menu_item = menu_item_response.json()

    # Update the menu item
    update_response = client.put(
        f"/restaurant/{restaurant['id']}/menu/{menu_item['id']}",
        json={
            "id": menu_item["id"],
            "name": "Updated Menu Item",
            "price": 7.99,
            "tags": ["test", "updated"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    updated_menu_item = update_response.json()

    assert updated_menu_item["name"] == "Updated Menu Item"
    assert updated_menu_item["price"] == 7.99
    assert updated_menu_item["tags"] == ["test", "updated"]

# test bulk creating menu items
def test_bulk_create_menu_items(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Bulk create menu items
    bulk_response = client.post(
        f"/restaurant/{restaurant['id']}/menu/bulk",
        json={
            "items": [
                {"name": "Bulk Item 1", "price": 10.99, "tags": ["test", "bulk"]},
                {"name": "Bulk Item 2", "price": 11.99, "tags": ["test", "bulk"]}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bulk_response.status_code == 201
    bulk_items = bulk_response.json()

    assert len(bulk_items) == 2
    assert bulk_items[0]["name"] == "Bulk Item 1"
    assert bulk_items[1]["name"] == "Bulk Item 2"

# test bulk updating menu items
def test_bulk_update_menu_items(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]

    # Create two menu items to update
    item1_response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Bulk Update Item 1",
            "price": 8.99,
            "tags": ["test", "bulk", "original"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    item2_response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={
            "name": "Bulk Update Item 2",
            "price": 9.99,
            "tags": ["test", "bulk", "original"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    item1 = item1_response.json()
    item2 = item2_response.json()

    # Bulk update the menu items
    bulk_update_response = client.put(
        f"/restaurant/{restaurant['id']}/menu/bulk",
        json={
            "items": [
                {"id": item1["id"], "name": "Updated Bulk Item 1", "price": 6.99, "tags": ["test", "bulk", "updated"]},
                {"id": item2["id"], "name": "Updated Bulk Item 2", "price": 7.99, "tags": ["test", "bulk", "updated"]}
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bulk_update_response.status_code == 200
    updated_items = bulk_update_response.json()

    assert len(updated_items) == 2
    assert updated_items[0]["name"] == "Updated Bulk Item 1"
    assert updated_items[0]["price"] == 6.99
    assert updated_items[0]["tags"] == ["test", "bulk", "updated"]
    assert updated_items[1]["name"] == "Updated Bulk Item 2"
    assert updated_items[1]["price"] == 7.99
    assert updated_items[1]["tags"] == ["test", "bulk", "updated"]