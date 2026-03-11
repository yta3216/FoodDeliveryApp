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
    assert len(results["results"]) == 1    
    assert results["results"][0]["name"] == "Test Restaurant"

# test searching for a restaurant by city
def test_search_restaurant_by_city():
    setup_restaurant()
    response = client.get("/restaurant/search?city=Kelowna")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 1    
    assert results["results"][0]["address"]["city"] == "Kelowna"

# test searching for a restaurant by menu item
def test_search_restaurant_by_menu_item():
    setup_restaurant()
    response = client.get("/restaurant/search?menu_item=Test Item 2")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 1    
    assert any(item["name"] == "Test Item 2" for item in results["results"][0]["menu"]["items"])

# test searching for a restaurant by name that does not exist
def test_search_restaurant_no_results():
    setup_restaurant()
    response = client.get("/restaurant/search?name=InvalidRestaurant")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 0

# test searching for a restaurant with multiple results
def test_search_restaurant_multiple_results():
    setup_restaurant()
    setup_restaurant(name="Test Restaurant", city="Vancouver")

    response = client.get("/restaurant/search?name=Test Restaurant")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 2
    assert all(result["name"] == "Test Restaurant" for result in results["results"])

# test searching for a restaurant by partial name
def test_search_restaurant_by_partial_name():
    setup_restaurant()
    response = client.get("/restaurant/search?name=Test")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 1    
    assert results["results"][0]["name"] == "Test Restaurant"

# test searching for a restaurant by partial menu item name
def test_search_restaurant_by_partial_menu_item():
    setup_restaurant()
    response = client.get("/restaurant/search?menu_item=Test Item")
    results = response.json()
    
    assert response.status_code == 200
    assert len(results["results"]) == 1    
    assert any("Test Item" in item["name"] for item in results["results"][0]["menu"]["items"])

# test that pagination metadata is returned correctly
def test_pagination_metadata_returned():
    setup_restaurant()
    response = client.get("/restaurant/search?name=Test Restaurant")
    results = response.json()

    assert response.status_code == 200
    assert "results" in results
    assert "total" in results
    assert "page" in results
    assert "page_size" in results
    assert "total_pages" in results

# test that page_size limits the number of results returned
def test_page_size_limits_results():
    for i in range(5):
        setup_restaurant(name=f"Pagination Test {i}", city="Kelowna")
    response = client.get("/restaurant/search?city=Kelowna&page_size=2")
    results = response.json()

    assert response.status_code == 200
    assert len(results["results"]) == 2
    assert results["page_size"] == 2

# test that page 2 returns a different set of results than page 1
def test_page_2_returns_different_results():
    for i in range(5):
        setup_restaurant(name=f"Pagination Test {i}", city="Kelowna")
    response_p1 = client.get("/restaurant/search?city=Kelowna&page=1&page_size=2")
    response_p2 = client.get("/restaurant/search?city=Kelowna&page=2&page_size=2")

    page1_ids = [r["id"] for r in response_p1.json()["results"]]
    page2_ids = [r["id"] for r in response_p2.json()["results"]]

    assert response_p1.status_code == 200
    assert response_p2.status_code == 200
    assert page1_ids != page2_ids

# test that total_pages is calculated correctly
def test_total_pages_calculated_correctly():
    for i in range(5):
        setup_restaurant(name=f"Pagination Test {i}", city="Kelowna")
    response = client.get("/restaurant/search?city=Kelowna&page_size=2")
    results = response.json()

    assert response.status_code == 200
    assert results["total"] == 5
    assert results["total_pages"] == 3  # ceil(5/2) = 3

# test that page 0 is rejected
def test_page_zero_rejected():
    response = client.get("/restaurant/search?page=0")
    assert response.status_code == 422

# test that page_size of 0 is rejected
def test_page_size_zero_rejected():
    response = client.get("/restaurant/search?page_size=0")
    assert response.status_code == 422

# test that page_size over 50 is rejected
def test_page_size_over_50_rejected():
    response = client.get("/restaurant/search?page_size=51")
    assert response.status_code == 422