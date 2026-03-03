""" This module implements business logic for restaurant management. """

from typing import List

from fastapi import HTTPException
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
    Restaurant_Search
)
from app.repositories.restaurant_repo import load_restaurants, save_restaurants

# Resturant address storage format
def _address_to_dict(address) -> dict:
    return{
        "street": address.street,
        "city": address.city,
        "province": address.province,
        "postal_code": address.postal_code
    }

# Create a new restaurant.
def create_restaurant(payload: Restaurant_Create, manager_id: str) -> Restaurant:
    restaurants = load_restaurants()
    new_id = max((restaurant.get("id", 0) for restaurant in restaurants), default=0) + 1 # generate unique ID for the new restaurant
    if any(restaurant.get("id") == new_id for restaurant in restaurants):
        raise HTTPException(status_code=409, detail="ID collision; retry.") # just in case, though should not be possible

    new_restaurant = {
        "id": new_id,
        "name": payload.name,
        "city": payload.city,
        "address": _address_to_dict(payload.address),
        "manager_ids": [manager_id],  # The logged in user is the initial manager of the restaurant
        "menu": {"items": payload.menu.items}
    }
    restaurants.append(new_restaurant)
    save_restaurants(restaurants)
    return Restaurant(**new_restaurant)

# Search for restaurants by name, city, or menu item.
def search_restaurants(payload: Restaurant_Search) -> List[Restaurant]:
    restaurants = load_restaurants()
    results = []
    for restaurant in restaurants:
        if payload.name and payload.name.lower() not in restaurant.get("name", "").lower():
            continue
        if payload.city and payload.city.lower() != restaurant.get("city", "").lower():
            continue
        if payload.menu_item:
            menu_items = [item for item in restaurant.get("menu", {}).get("items", [])]
            if not any(payload.menu_item.lower() in item.get("name", "").lower() for item in menu_items):
                continue

        results.append(Restaurant(**restaurant))
    return results

# Update restaurant details (name, city, address)
def update_restaurant_details(payload: Restaurant_Details_Update) -> Restaurant:
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == payload.id:
            restaurant["name"] = payload.name.strip()
            restaurant["city"] = payload.city.strip()
            restaurant["address"] = _address_to_dict(payload.address)
            save_restaurants(restaurants)
            return Restaurant(**restaurant)
    raise HTTPException(status_code=404, detail=f"Restaurant '{payload.id}' not found")

# Update restaurant managers
def update_restaurant_managers(payload: Restaurant_Managers_Update) -> Restaurant:
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == payload.id:
            restaurant["manager_ids"] = [manager_id.strip() for manager_id in payload.manager_ids]
            save_restaurants(restaurants)
            return Restaurant(**restaurant)
    raise HTTPException(status_code=404, detail=f"Restaurant '{payload.id}' not found")

# Create a new menu item and add it to the restaurant's menu.
def create_menu_item(restaurant_id: int, payload: MenuItem_Create) -> MenuItem:
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

# Update an existing menu item in the restaurant's menu.
def update_menu_item(restaurant_id: int, payload: MenuItem_Update) -> MenuItem:
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

# Bulk create menu items and add them to the restaurant's menu.
def bulk_menu_item_create(restaurant_id: int, payload: MenuItem_Bulk_Create) -> List[MenuItem]:
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

# Bulk update menu items in the restaurant's menu.
def bulk_menu_item_update(restaurant_id: int, payload: MenuItem_Bulk_Update) -> List[MenuItem]:
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