"""
This module defines the API routes for restaurant management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

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
    MenuItem_Bulk_Update,
    Restaurant_Search,
    PaginatedRestaurantResults
)

from app.auth import require_role
from app.services.restaurant_service import (
    create_restaurant,
    search_restaurants,
    update_restaurant_details,
    update_restaurant_managers,
    create_menu_item,
    update_menu_item,
    bulk_menu_item_create,
    bulk_menu_item_update,
    check_manager
)

router = APIRouter(prefix="/restaurant", tags=["restaurant"])

# post request to create a new restaurant. Uses logged in user as the initial manager. Only managers can create restaurants.
@router.post("", response_model=Restaurant, status_code=201)
def create_restaurant_route(payload: Restaurant_Create, current_user: User = Depends(require_role((UserRole.RESTAURANT_MANAGER)))):
    return create_restaurant(payload, current_user.id)

# post request to search for restaurants by name, address fields, or menu item.
# every field is optional and no authentication is required to search for restaurants.
@router.get("/search", response_model=PaginatedRestaurantResults)
def search_restaurants_route(
    name: str | None = None,
    city: str | None = None,
    street: str | None = None,
    province: str | None = None,
    postal_code: str | None = None,
    menu_item: str | None = None,
    sort_price: str | None = None,
    page: int = 1,
    page_size: int = 5
):
    # catch validation errors from the search schema and return 422
    try:
        payload = Restaurant_Search(
            name=name,
            city=city,
            street=street,
            province=province,
            postal_code=postal_code,
            menu_item=menu_item,
            sort_price=sort_price,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return search_restaurants(payload)

# put request to update restaurant details (name, city, address)
@router.put("/{restaurant_id}", response_model=Restaurant, dependencies=[Depends(check_manager)])
def update_restaurant_details_route(restaurant_id: int, payload: Restaurant_Details_Update):
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_details(payload)

# put request to update restaurant managers. only managers can update restaurant managers.
@router.put("/{restaurant_id}/managers", response_model=Restaurant, dependencies=[Depends(check_manager)])
def update_restaurant_managers_route(restaurant_id: int, payload: Restaurant_Managers_Update):
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_managers(payload)

# post request to bulk create menu items in the restaurant's menu. only managers can bulk create menu items.
@router.post("/{restaurant_id}/menu/bulk", response_model=List[MenuItem], status_code=201, dependencies=[Depends(check_manager)])
def bulk_create_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Create):
    return bulk_menu_item_create(restaurant_id, payload)

# put request to bulk update menu items in the restaurant's menu. only managers can bulk update menu items.
@router.put("/{restaurant_id}/menu/bulk", response_model=List[MenuItem], dependencies=[Depends(check_manager)])
def bulk_update_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Update):
    return bulk_menu_item_update(restaurant_id, payload)

# post request to create a new menu item and add it to the restaurant's menu. only managers can add menu items.
@router.post("/{restaurant_id}/menu", response_model=MenuItem, status_code=201, dependencies=[Depends(check_manager)])
def create_menu_item_route(restaurant_id: int, payload: MenuItem_Create):
    return create_menu_item(restaurant_id, payload)

# put request to update a menu item in the restaurant's menu. only managers can update menu items.
@router.put("/{restaurant_id}/menu/{menu_item_id}", response_model=MenuItem, dependencies=[Depends(check_manager)])
def update_menu_item_route(restaurant_id: int, menu_item_id: int, payload: MenuItem_Update):
    if menu_item_id != payload.id:
        raise HTTPException(status_code=400, detail="Menu item ID in path and body must match")
    return update_menu_item(restaurant_id, payload)
