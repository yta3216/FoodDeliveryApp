"""testing restaurant validation"""
from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.schemas.user_schema import UserRole

client = TestClient(app)

VALID_RESTAURANT_ADDRESS = {
    "street": "123 Main St",
    "city": "Kelowna",
    "province": "BC",
    "postal_code": "A1A 1A1"
}

# helper to create a manager and get a token
def get_manager_token(email):
    client.post("/user", json={
        "email": email,
        "password": "testpassword",
        "name": "Test Manager",
        "age": 30,
        "gender": "female",
        "role": "manager",
    })
    login = client.post("/user/login", json={"email": email, "password": "testpassword"})
    return login.json()["token"]

# helper to create a restaurant and return it
def create_restaurant(token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Test Restaurant",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

@pytest.fixture
def manager_token():
    user = client.post(
        "/user",
        json={
            "email": "addrvalidator@example.com",
            "password": "testpassword",
            "name": "Address Validator",
            "age": 28,
            "gender": "other",
            "role": "manager",
        }
    )
    assert user.status_code == 201
    login = client.post("/user/login", json={"email": "addrvalidator@example.com", "password": "testpassword"})
    assert login.status_code == 200
    return login.json()["token"]


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
            "address": VALID_RESTAURANT_ADDRESS
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restaurant_response.status_code == 403  # Forbidden due to wrong role

# ------- RESTAURANT FIELD VALIDATION TESTS ------- #

# test that empty restaurant name is rejected
def test_empty_restaurant_name_rejected():
    token = get_manager_token("emptyname@example.com")
    response = client.post(
        "/restaurant",
        json={
            "name": "",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# test that restaurant name with only whitespace is rejected
def test_whitespace_restaurant_name_rejected():
    token = get_manager_token("whitespace@example.com")
    response = client.post(
        "/restaurant",
        json={
            "name": "   ",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# test that a restaurant with an invalid city is rejected
def test_empty_city_rejected():
    token = get_manager_token("emptycity@example.com")
    response = client.post(
        "/restaurant",
        json={
            "name": "Test Restaurant",
            "city": "",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# test that an invalid restaurant field returns an error message that includes the field name
def test_invalid_restaurant_field_returns_error_message():
    token = get_manager_token("errormsg@example.com")
    response = client.post(
        "/restaurant",
        json={
            "name": "",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    # check that the error response tells the user which field is wrong
    errors = response.json()["detail"]
    fields = [e["loc"][-1] for e in errors]
    assert "name" in fields

# ------- MENU ITEM FIELD VALIDATION TESTS ------- #

# test that a valid menu item can be created successfully
def test_valid_menu_item_accepted():
    token = get_manager_token("validmenu@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Burger", "price": 9.99, "tags": ["popular"]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Burger"
    assert response.json()["price"] == 9.99

# test that a menu item with price 0 (free) is accepted
def test_zero_price_accepted():
    token = get_manager_token("zeroprice@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Free Item", "price": 0.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

# test that a menu item with an empty name is rejected
def test_empty_menu_item_name_rejected():
    token = get_manager_token("menuname@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# test that a menu item with price less than 0 is rejected
def test_negative_price_rejected():
    token = get_manager_token("negativeprice@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Burger", "price": -1.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# test that an invalid menu item field returns an error message that includes the field name
def test_invalid_menu_item_field_returns_error_message():
    token = get_manager_token("errormsgmenu@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    fields = [e["loc"][-1] for e in errors]
    assert "name" in fields

# ------- MENU ITEM UPDATE VALIDATION TESTS ------- #

def test_empty_menu_item_name_on_update_rejected():
    token = get_manager_token("updatemenu@example.com")
    restaurant = create_restaurant(token)
    # create a menu item first
    item = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Burger", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    # try to update with empty name
    response = client.put(
        f"/restaurant/{restaurant['id']}/menu/{item['id']}",
        json={"id": item["id"], "name": "", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

def test_negative_price_on_update_rejected():
    token = get_manager_token("updateprice@example.com")
    restaurant = create_restaurant(token)
    item = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Burger", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    ).json()
    response = client.put(
        f"/restaurant/{restaurant['id']}/menu/{item['id']}",
        json={"id": item["id"], "name": "Burger", "price": -5.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# ------- ADDRESS VALIDATION TESTS ------- #

# Test valid address - all fields
def test_create_restaurant_valid_address(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    addr = response.json()["address"]
    assert addr["street"] == "456 Centre St"
    assert addr["city"] == "Kelowna"
    assert addr["province"] == "BC"
    assert addr["postal_code"] == "T2P 1A1"

# Test invalid Postal code format
def test_create_restaurant_postal_code_normalised(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "aaaaaa"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 422

# Test province code case insensitivity - should be accepted in lowercase and stored in uppercase
def test_create_restaurant_province_case_insensitive(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "bc",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["address"]["province"] == "BC"

# Test Invalid province code
def test_create_restaurant_invalid_province(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "XX",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 422

# Test street without a leading number
def test_create_restaurant_street_no_number(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "Centre St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 422

# Test empty street
def test_create_restaurant_empty_street(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 422

# Test empty city
def test_create_restaurant_empty_city_in_address(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "",
                "province": "BC",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 422

# Test invalid province code on update
def test_update_restaurant_invalid_province(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "XX",
                "postal_code": "T2P 1A1"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# Test invalid postal code format on update
def test_update_restaurant_invalid_postal_code(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "name": "Koi Sushi",
            "city": "Kelowna",
            "address": {
                "street": "456 Centre St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "aaaaaa"
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

# ------- MAX DELIVERY RADIUS VALIDATION TESTS ------- #

# test that a restaurant is created with the default delivery radius if none is provided
def test_create_restaurant_default_delivery_radius(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Radius Test Place",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["max_delivery_radius_km"] == 10.0

# test that a restaurant is created with a custom delivery radius
def test_create_restaurant_custom_delivery_radius(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Custom Radius Place",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            },
            "max_delivery_radius_km": 25.0
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["max_delivery_radius_km"] == 25.0

# test that delivery radius is updated when restaurant details are updated
def test_update_restaurant_delivery_radius(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": restaurant["name"],
            "city": restaurant["city"],
            "address": restaurant["address"],
            "max_delivery_radius_km": 50.0
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["max_delivery_radius_km"] == 50.0

# ------- DELIVERY FEE VALIDATION TESTS ------- #

# test that a restaurant is given the default delivery fee if none is provided
def test_create_restaurant_default_delivery_fee(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Radius Test Place",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            }
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["delivery_fee"] == 0.0

# test that a restaurant is created with a custom delivery fee
def test_create_restaurant_custom_delivery_fee(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Custom Radius Place",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            },
            "delivery_fee": 4.99
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["delivery_fee"] == 4.99

# test that a restaurant's custom delivery fee is rounded
def test_create_restaurant_custom_delivery_fee_rounded(manager_token):
    response = client.post(
        "/restaurant",
        json={
            "name": "Custom Radius Place",
            "city": "Kelowna",
            "address": {
                "street": "123 Main St",
                "city": "Kelowna",
                "province": "BC",
                "postal_code": "V1Y 1A1"
            },
            "delivery_fee": 6.759
        },
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 201
    assert response.json()["delivery_fee"] == 6.76

# test that delivery fee is updated when restaurant details are updated
def test_update_restaurant_delivery_fee(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": restaurant["name"],
            "city": restaurant["city"],
            "address": restaurant["address"],
            "delivery_fee": 6.76
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["delivery_fee"] == 6.76

# test that the updated delivery fee is rounded
def test_update_restaurant_delivery_fee_rounded(setup_restaurant):
    restaurant = setup_restaurant["restaurant"]
    token = setup_restaurant["token"]
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
            "name": restaurant["name"],
            "city": restaurant["city"],
            "address": restaurant["address"],
            "delivery_fee": 6.7559
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["delivery_fee"] == 6.76
