""" testing restaurant creation."""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.schemas.user_schema import UserRole

client = TestClient(app)

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
            "address": "123 Test St"
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

# test a restaurant creation attempt with the wrong role
def test_create_restaurant_wrong_role():
    # First, create a user who is not a valid restaurant manager
    test_user = client.post(
        "/user", 
        json={
            "email": "wrongrole@example.com",
            "password": "testpassword",
            "name": "Wrong Role",
            "age": 40,
            "gender": "male",
            "role": UserRole.CUSTOMER,  # This user is not a manager
        }
    )
    assert test_user.status_code == 201
    
    # Log in as the user with wrong role
    login_response = client.post(
        "/user/login",
        json={
            "email": "wrongrole@example.com",
            "password": "testpassword",
        }
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    token = login_data["token"]

    # Try to create a restaurant with the wrong role user
    restaurant_response = client.post(
        "/restaurant",
        json={
            "name": "Test Restaurant",
            "city": "Test City",
            "address": "456 Test St"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restaurant_response.status_code == 403  # Forbidden due to wrong role

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
            "address": "789 Test St"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    updated_restaurant = update_response.json()
    assert updated_restaurant["name"] == "Updated Restaurant"

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