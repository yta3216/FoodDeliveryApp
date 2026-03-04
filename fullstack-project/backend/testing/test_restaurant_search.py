from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_RESTAURANT_ADDRESS = {
    "street": "123 Main St",
    "city": "Kelowna",
    "province": "BC",
    "postal_code": "A1A 1A1"
}

# helper function to set up a restaurant for testing
def setup_restaurant(name = "Test Restaurant", city = "Kelowna", address = VALID_RESTAURANT_ADDRESS, menu_items = None):
    # Create a test user with manager role

    test_manager = client.post(
        "/user",
        json={
            "email": "search@example.com",
            "password": "testpassword",
            "name": "Test Manager",
            "age": 25,
            "gender": "male",
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
            "name": name,
            "city": city,
            "address": address,
            "menu": {
                "items": menu_items or [
                    {"name": "Test Item 1", "description": "Description of Test Item 1", "price": 9.99},
                    {"name": "Test Item 2", "description": "Description of Test Item 2", "price": 14.99}
                ]
            }
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert restaurant_response.status_code == 201

    return {
        "restaurant": restaurant_response.json(),
        "token": token
    }

# test searching for a restaurant by name
def test_search_restaurant_by_name():
    setup_restaurant()
    response = client.get("/restaurant/search?name=Test Restaurant")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 1    
    assert results[0]["name"] == "Test Restaurant"

# test searching for a restaurant by city
def test_search_restaurant_by_city():
    setup_restaurant()
    response = client.get("/restaurant/search?city=Kelowna")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 1    
    assert results[0]["address"]["city"] == "Kelowna"

# test searching for a restaurant by menu item
def test_search_restaurant_by_menu_item():
    setup_restaurant()
    response = client.get("/restaurant/search?menu_item=Test Item 2")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 1    
    assert any(item["name"] == "Test Item 2" for item in results[0]["menu"]["items"])

# test searching for a restaurant by name that does not exist
def test_search_restaurant_no_results():
    setup_restaurant()
    response = client.get("/restaurant/search?name=InvalidRestaurant")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 0

# test searching for a restaurant with multiple results
def test_search_restaurant_multiple_results():
    setup_restaurant()
    setup_restaurant(name="Test Restaurant", city="Vancouver")

    response = client.get("/restaurant/search?name=Test Restaurant")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 2
    assert all(result["name"] == "Test Restaurant" for result in results)

# test searching for a restaurant by partial name
def test_search_restaurant_by_partial_name():
    setup_restaurant()
    response = client.get("/restaurant/search?name=Test")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 1    
    assert results[0]["name"] == "Test Restaurant"

# test searching for a restaurant by partial menu item name
def test_search_restaurant_by_partial_menu_item():
    setup_restaurant()
    response = client.get("/restaurant/search?menu_item=Test Item")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results) == 1    
    assert any("Test Item" in item["name"] for item in results[0]["menu"]["items"])

# test that sorting by distance asc returns the closest restaurant first
def test_sort_by_distance_asc():
    # kelowna coords: (49.8880, -119.4960)
    # vancouver coords: (49.2827, -123.1207)
    # assume user is in kelowna, so kelowna restaurant should come first
    setup_restaurant(name="Kelowna Place", city="Kelowna")
    setup_restaurant(name="Vancouver Place", city="Vancouver")

    response = client.get("/restaurant/search?sort_distance=asc&user_lat=49.8880&user_lng=-119.4960")
    results = response.json()

    assert response.status_code == 200
    assert len(results) >= 2
    cities = [r["city"] for r in results]
    assert cities.index("Kelowna") < cities.index("Vancouver")

# test that sorting by distance desc returns the furthest restaurant first
def test_sort_by_distance_desc():
    setup_restaurant(name="Kelowna Place", city="Kelowna")
    setup_restaurant(name="Vancouver Place", city="Vancouver")

    response = client.get("/restaurant/search?sort_distance=desc&user_lat=49.8880&user_lng=-119.4960")
    results = response.json()

    assert response.status_code == 200
    assert len(results) >= 2
    cities = [r["city"] for r in results]
    assert cities.index("Vancouver") < cities.index("Kelowna")

# test that passing invalid sort_distance value returns 422
def test_sort_by_distance_invalid_value():
    response = client.get("/restaurant/search?sort_distance=invalid")
    assert response.status_code == 422

# test that sort_distance without user coords just returns results unsorted
def test_sort_by_distance_missing_coords():
    setup_restaurant(name="Kelowna Place", city="Kelowna")
    response = client.get("/restaurant/search?sort_distance=asc")
    assert response.status_code == 200
