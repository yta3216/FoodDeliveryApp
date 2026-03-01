""" This module implements business logic for restaurant management. """

from fastapi import HTTPException
from app.schemas.restaurant_schema import (
    Restaurant, 
    Restaurant_Create, 
    Restaurant_Details_Update, 
    Restaurant_Managers_Update,
)
from app.repositories.restaurant_repo import load_restaurants, save_restaurants

# Create a new restaurant with an empty menu.
def create_restaurant(payload: Restaurant_Create, manager_id: str) -> Restaurant:
    restaurants = load_restaurants()
    new_id = max((restaurant.get("id", 0) for restaurant in restaurants), default=0) + 1 # generate unique ID for the new restaurant
    if any(restaurant.get("id") == new_id for restaurant in restaurants):
        raise HTTPException(status_code=409, detail="ID collision; retry.") # just in case, though should not be possible

    new_restaurant = {
        "id": new_id,
        "name": payload.name.strip(),
        "city": payload.city.strip(),
        "address": payload.address.strip(),
        "manager_ids": [manager_id], # The logged in user is the initial manager of the restaurant
        "menu": [] # Start with an empty menu
    }
    restaurants.append(new_restaurant)
    save_restaurants(restaurants)
    return Restaurant(**new_restaurant)

# Update restaurant details (name, city, address)
def update_restaurant_details(payload: Restaurant_Details_Update) -> Restaurant:
    restaurants = load_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == payload.id:
            restaurant["name"] = payload.name.strip()
            restaurant["city"] = payload.city.strip()
            restaurant["address"] = payload.address.strip()
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
