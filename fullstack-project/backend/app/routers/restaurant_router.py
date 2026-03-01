"""
This module defines the API routes for restaurant management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_role
from app.schemas.user_schema import User, UserRole
from app.schemas.restaurant_schema import (
    Restaurant,
    Restaurant_Create,
    Restaurant_Details_Update,
    Restaurant_Managers_Update,
    MenuItem,
    MenuItem_Create,
    MenuItem_Update,
    MenuItem_Bulk_Create,
    MenuItem_Bulk_Update
)

from app.services.restaurant_service import (
    create_restaurant,
    update_restaurant_details,
    update_restaurant_managers,
    create_menu_item,
    update_menu_item,
    bulk_menu_item_create,
    bulk_menu_item_update
)

router = APIRouter(prefix="/restaurant", tags=["restaurant"])

# post request to create a new restaurant. Uses logged in user as the initial manager.
@router.post("", response_model=Restaurant, status_code=201)
def create_restaurant_route(payload: Restaurant_Create):
    current_user = require_role(UserRole.RESTAURANT_MANAGER) # only restaurant managers can create restaurants
    return create_restaurant(payload, current_user.id)

# put request to update restaurant details (name, city, address)
@router.put("/{restaurant_id}", response_model=Restaurant)
def update_restaurant_details_route(restaurant_id: int, payload: Restaurant_Details_Update):
    require_role(UserRole.RESTAURANT_MANAGER) # only restaurant managers can update restaurant details
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_details(payload)

# put request to update restaurant managers
@router.put("/{restaurant_id}/managers", response_model=Restaurant)
def update_restaurant_managers_route(restaurant_id: int, payload: Restaurant_Managers_Update):
    require_role(UserRole.RESTAURANT_MANAGER) # only restaurant managers can update restaurant managers
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_managers(payload)

# post request to create a new menu item and add it to the restaurant's menu
@router.post("/{restaurant_id}/menu", response_model=MenuItem, status_code=201)
def create_menu_item_route(restaurant_id: int, payload: MenuItem_Create):
    require_role(UserRole.MANAGER) # only managers can add menu items
    return create_menu_item(restaurant_id, payload)

# put request to update a menu item in the restaurant's menu
@router.put("/{restaurant_id}/menu/{menu_item_id}", response_model=MenuItem)
def update_menu_item_route(restaurant_id: int, menu_item_id: int, payload: MenuItem_Update):
    require_role(UserRole.MANAGER) # only managers can update menu items
    if menu_item_id != payload.id:
        raise HTTPException(status_code=400, detail="Menu item ID in path and body must match")
    return update_menu_item(restaurant_id, payload)

# post request to bulk create menu items in the restaurant's menu
@router.post("/{restaurant_id}/menu/bulk", response_model=List[MenuItem], status_code=201)
def bulk_create_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Create):
    require_role(UserRole.MANAGER) # only managers can bulk create menu items
    return bulk_menu_item_create(restaurant_id, payload)

# put request to bulk update menu items in the restaurant's menu
@router.put("/{restaurant_id}/menu/bulk", response_model=List[MenuItem])
def bulk_update_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Update):
    require_role(UserRole.MANAGER) # only managers can bulk update menu items
    return bulk_menu_item_update(restaurant_id, payload)