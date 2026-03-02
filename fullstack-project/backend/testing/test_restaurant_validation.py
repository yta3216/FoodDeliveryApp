"""testing restaurant and menu item input validation"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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


# restaurant name validation

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


# menu item validation

def test_empty_menu_item_name_rejected():
    token = get_manager_token("menuname@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "", "price": 9.99, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

def test_negative_price_rejected():
    token = get_manager_token("negativeprice@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Burger", "price": -1.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422

def test_zero_price_accepted():
    token = get_manager_token("zeroprice@example.com")
    restaurant = create_restaurant(token)
    response = client.post(
        f"/restaurant/{restaurant['id']}/menu",
        json={"name": "Free Item", "price": 0.00, "tags": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201

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

def test_empty_name_on_update_rejected():
    token = get_manager_token("updateemptyname@example.com")
    restaurant = create_restaurant(token)
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
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

def test_empty_city_on_update_rejected():
    token = get_manager_token("updateemptycity@example.com")
    restaurant = create_restaurant(token)
    response = client.put(
        f"/restaurant/{restaurant['id']}",
        json={
            "id": restaurant["id"],
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