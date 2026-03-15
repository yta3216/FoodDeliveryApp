""" This module implements business logic for restaurant management. """

from fastapi import Depends, HTTPException
from app.schemas.restaurant_schema import (
    Restaurant, 
    Restaurant_Create, 
    Restaurant_Details_Update, 
    Restaurant_Managers_Update,
    MenuItem,
    MenuItem_Create,
    MenuItem_Update,
    MenuItem_Bulk_Create,
    MenuItem_Bulk_Update,
    Restaurant_Search,
    PaginatedRestaurantResults
)
from app.repositories.restaurant_repo import load_restaurants, save_restaurants
from app.auth import require_role
from app.schemas.user_schema import User, UserRole

def _address_to_dict(address) -> dict:
    """Converts an Address object to a dictionary."""
    return {
        "street": address.street,
        "city": address.city,
        "province": address.province,
        "postal_code": address.postal_code
    }

def _calculate_average_price(restaurant: dict) -> float:
    """
    Computes the average price of all menu items for a given restaurant dictionary.

    Parameters:
        restaurant (dict): the restaurant whose average item price is desired
    
    Returns:
        float: the average price of all menu items, 0 if no menu items exist
    """
    items = restaurant.get("menu",{}).get("items", [])
    if not items:
        return 0.0
    total_price = sum(item.get("price", 0) for item in items)
    return total_price / len(items)

def get_new_id(restaurants) -> int:
    """
    Generates the next available id for the next restaurant to be created based on the given list of restaurants.

    Parameters:
        restaurants (list[dict]): list of all restaurants in restaurants.json
    
    Returns:
        int: the next available restaurant id
    """
    new_id = max((restaurant.get("id", 0) for restaurant in restaurants), default=0) + 1
    if any(restaurant.get("id") == new_id for restaurant in restaurants):
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    return new_id

# Create a new restaurant.
def create_restaurant(payload: Restaurant_Create, manager_id: str) -> Restaurant:
    """
    Creates a new restaurant and saves it to restaurants.json.
    Assigns the passed in manager id as the initial manager of the restaurant.

    Parameters:
        payload (Restaurant_Create): the details of the restaurant to be created
        manager_id (str): the current logged-in user. must have role manager

    Returns:   
        Restaurant: the newly created restaurant
    """
    restaurants = load_restaurants()
    new_id = get_new_id(restaurants)

    new_restaurant = {
        "id": new_id,
        "name": payload.name,
        "city": payload.city,
        "address": _address_to_dict(payload.address),
        "manager_ids": [manager_id],
        "max_delivery_radius_km": payload.max_delivery_radius_km,
        "menu": {"items": [{
            "id": idx + 1, **item.model_dump()}
            for idx, item in enumerate(payload.menu.items)
        ]}
    }
    restaurants.append(new_restaurant)
    save_restaurants(restaurants)
    return Restaurant(**new_restaurant)

def search_restaurants(payload: Restaurant_Search) -> PaginatedRestaurantResults:
    """
    Searches for restaurants by the filters provided in Restaurant_Search.
    May be sorted ascending, descending, or not sorted at all, depending on what is specified in payload.

    Parameters:
        payload (Restaurant_Search): the search critera, which may include name, address, menu item, etc.
    
    Returns:
        PaginatedSearchResults: the restaurant search results in paginated form
    """
    restaurants = load_restaurants()
    results = []
    for restaurant in restaurants:
        if payload.name and payload.name.lower() not in restaurant.get("name", "").lower():
            continue
        if payload.city and payload.city.lower() not in restaurant.get("city", "").lower():
            continue
        addr = restaurant.get("address", {})
        if payload.street and payload.street.lower() not in addr.get("street", "").lower():
            continue
        if payload.province and payload.province.upper() != addr.get("province", "").upper():
            continue
        if payload.postal_code and payload.postal_code.lower() not in addr.get("postal_code", "").lower():
            continue
        if payload.menu_item:
            menu_items = restaurant.get("menu", {}).get("items", [])
            if not any(payload.menu_item.lower() in item.get("name", "").lower() for item in menu_items):
                continue
        results.append(restaurant)

    if payload.sort_price == "asc":
        results.sort(key=_calculate_average_price)
    elif payload.sort_price == "desc":
        results.sort(key=_calculate_average_price, reverse=True)

    total = len(results)
    total_pages = max(1, -(-total // payload.page_size))
    start = (payload.page - 1) * payload.page_size
    end = start + payload.page_size
    page_results = [Restaurant(**r) for r in results[start:end]]

    return PaginatedRestaurantResults(
        results=page_results,
        total=total,
        page=payload.page,
        page_size=payload.page_size,
        total_pages=total_pages
    )


# Update restaurant details (name, city, address)
def update_restaurant_details(payload: Restaurant_Details_Update) -> Restaurant:
    """
    Updates the restaurant's details such as name, city, address, or maximum delivery radius.

    Parameters:
        payload (Restaurant_Details_Update): the updated restaurant details

    Returns:
        Restaurant: the restaurant with updated details

    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == payload.id:
            restaurant["name"] = payload.name.strip()
            restaurant["city"] = payload.city.strip()
            restaurant["address"] = _address_to_dict(payload.address)
            restaurant["max_delivery_radius_km"] = payload.max_delivery_radius_km
            save_restaurants(restaurants)
            return Restaurant(**restaurant)
    raise HTTPException(status_code=404, detail=f"Restaurant '{payload.id}' not found")

def update_restaurant_managers(payload: Restaurant_Managers_Update) -> Restaurant:
    """
    Updates a restaurant's list of approved managers. Overwrites the existing list with the new one.

    Parameters:
        payload (Restaurant_Managers_Update): the new list of restaurant managers
    
    Returns:
        Restaurant: the restaurant with an updated list of managers
    
    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == payload.id:
            restaurant["manager_ids"] = [manager_id.strip() for manager_id in payload.manager_ids]
            save_restaurants(restaurants)
            return Restaurant(**restaurant)
    raise HTTPException(status_code=404, detail=f"Restaurant '{payload.id}' not found")

def create_menu_item(restaurant_id: int, payload: MenuItem_Create) -> MenuItem:
    """
    Creates a new menu item and adds it to the provided restaurant's menu.

    Parameters:
        restaurant_id (int): the identifier of the restaurant to receive this new item
        payload (MenuItem_Create): the details of the menu item to be created

    Returns:
        MenuItem: the newly created menu item
    
    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """

    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            new_item_id = max((item.get("id", 0) for item in restaurant["menu"]["items"]), default=0) + 1
            new_item = {
                "id": new_item_id,
                "name": payload.name.strip(),
                "price": payload.price,
                "tags": [tag.strip() for tag in payload.tags]
            }
            restaurant["menu"]["items"].append(new_item)
            save_restaurants(restaurants)
            return MenuItem(**new_item)
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")

def update_menu_item(restaurant_id: int, payload: MenuItem_Update) -> MenuItem:
    """
    Updates an existing menu item in the provided restaurant's menu.

    Parameters:
        restaurant_id (int): the identifier of the restaurant containing the item to be updated
        payload (MenuItem_Update): the details of the menu item and associated updates

    Returns:
        MenuItem: the newly updated menu item

    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json or menu item not found in restaurant
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            for item in restaurant["menu"]["items"]:
                if item.get("id") == payload.id:
                    item["name"] = payload.name.strip()
                    item["price"] = payload.price
                    item["tags"] = [tag.strip() for tag in payload.tags]
                    save_restaurants(restaurants)
                    return MenuItem(**item)
            raise HTTPException(status_code=404, detail=f"Menu item '{payload.id}' not found in restaurant '{restaurant_id}'")
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")

def bulk_menu_item_create(restaurant_id: int, payload: MenuItem_Bulk_Create) -> list[MenuItem]:
    """
    Creates several new menu items and adds them to the provided restaurant's menu.

    Parameters:
        restaurant_id (int): the identifier of the restaurant to receive these new items
        payload (MenuItem_Bulk_Create): the details of the menu items to be created

    Returns:
        list[MenuItem]: the newly created menu items

    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            new_items = []
            for item_payload in payload.items:
                new_item_id = max((item.get("id", 0) for item in restaurant["menu"]["items"]), default=0) + 1
                new_item = {
                    "id": new_item_id,
                    "name": item_payload.name.strip(),
                    "price": item_payload.price,
                    "tags": [tag.strip() for tag in item_payload.tags]
                }
                restaurant["menu"]["items"].append(new_item)
                new_items.append(MenuItem(**new_item))
            save_restaurants(restaurants)
            return new_items
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")

def bulk_menu_item_update(restaurant_id: int, payload: MenuItem_Bulk_Update) -> list[MenuItem]:
    """
    Updates several existing menu items in the provided restaurant's menu.

    Parameters:
        restaurant_id (int): the identifier of the restaurant containing the items to be updated
        payload (MenuItem_Bulk_Update): the details of the menu items and associated updates

    Returns:
        list[MenuItem]: the newly updated menu items

    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json or menu item not found in restaurant
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            updated_items = []
            for item_payload in payload.items:
                for item in restaurant["menu"]["items"]:
                    if item.get("id") == item_payload.id:
                        item["name"] = item_payload.name.strip()
                        item["price"] = item_payload.price
                        item["tags"] = [tag.strip() for tag in item_payload.tags]
                        updated_items.append(MenuItem(**item))
                        break
                else:
                    raise HTTPException(status_code=404, detail=f"Menu item '{item_payload.id}' not found in restaurant '{restaurant_id}'")
            save_restaurants(restaurants)
            return updated_items
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")

def get_restaurant_by_id(restaurant_id: int) -> Restaurant:
    """
    Retrieves the restaurant with matching id to the provided id.

    Parameters:
        restaurant_id (int): the identifier of the restaurant to be retrieved
    
    Returns:
        Restaurant: the restaurant from restaurants.json whose id matches the provided id

    Raises:
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            return restaurant
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")

def check_manager(restaurant_id: int, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))) -> User:
    """
    Checks that the current logged in user has role "manager" and is a manager of the restaurant with the provided id.

    Parameters:
        restaurant_id (int): the identifier of the restaurant whose manager is to be verified
        current_user (User): the authenticated user who is automatically passed as an argument. must have role "manager".
    
    Returns:
        User: the details of the manager being verified

    Raises:
        HTTPException (status_code = 401): if user's token is invalid or expired
        HTTPException (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            if current_user.id in restaurant.get("manager_ids"):
                return current_user # user is a manager of the restaurant
            raise HTTPException(status_code=403, detail="User is not a manager of this restaurant")
    raise HTTPException(status_code=404, detail=f"Restaurant '{restaurant_id}' not found")
