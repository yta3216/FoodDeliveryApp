"""
This module defines the API routes for restaurant management.
Most functions use check_manager as a dependency, which will
authenticate the user and verify they are a manager of the
specified restaurant.
"""

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
from app.services.order_service import get_orders_for_restaurant
from app.schemas.order_schema import Order

router = APIRouter(prefix="/restaurant", tags=["restaurant"])

@router.post("", response_model=Restaurant, status_code=201)
def create_restaurant_route(payload: Restaurant_Create, current_user: User = Depends(require_role((UserRole.RESTAURANT_MANAGER)))):
    """
    **Creates a new restaurant, assigning the logged-in manager as the intial manger for the new restaurant.**
    
    Parameters:
    *   **payload** (Restaurant_Create): the details of the restaurant to be created
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **Restaurant**: the newly created restaurant

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role does not match the requested role
    """
    return create_restaurant(payload, current_user.id)

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
    """
    **Searches restaurants by various optional fields. Does not require authentication.**
    
    Parameters: *(all optional)*
    *   **name** (str): restaurant name
    *   **city** (str): restaurant city
    *   **street** (str): restaurant street
    *   **province** (str): restaurant province
    *   **postal_code** (str): restaurant postal code
    *   **menu_item** (str): menu item name
    *   **sort_price** (str): "asc" or "desc" for ascending or descending results

    Returns:
    *   **PaginatedRestaurantResults**: a paginated response of restaurants satisfying this criteria

    Raises:
    *   **HTTPException** (status_code = 422): arguments do not match Restaurant_Search schema
    """
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

@router.put("/{restaurant_id}", response_model=Restaurant, dependencies=[Depends(check_manager)])
def update_restaurant_details_route(restaurant_id: int, payload: Restaurant_Details_Update):
    """
    **Updates a restaurant's details such as name, city, or address. Must be one of the restaurant managers to use.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to be updated
    *   **payload** (Restaurant_Details_Update): the updated restaurant details

    Returns:
    *   **Restaurant**: the modified restaurant

    Raises:
    *   **HTTPException** (status_code = 400): restaurant_id in payload and URL do not match
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_details(payload)

@router.patch("/{restaurant_id}/managers", response_model=Restaurant, dependencies=[Depends(check_manager)])
def update_restaurant_managers_route(restaurant_id: int, payload: Restaurant_Managers_Update):
    """
    **Updates a restaurant's list of managers. Must be one of the restaurant managers to use.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to be updated
    *   **payload** (Restaurant_Managers_Update): the new complete list of restaurant managers

    Returns:
    *   **Restaurant**: the modified restaurant

    Raises:
    *   **HTTPException** (status_code = 400): restaurant_id in payload and URL do not match
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_managers(payload)

@router.post("/{restaurant_id}/menu/bulk", response_model=list[MenuItem], status_code=201, dependencies=[Depends(check_manager)])
def bulk_create_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Create):
    """
    **Adds multiple new items to a restaurant's menu at once. Must be one of the restaurant managers to use.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to be updated
    *   **payload** (MenuItem_Bulk_Create): all new menu items

    Returns:
    *   **list[MenuItem]**: a list of the newly created menu items

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    return bulk_menu_item_create(restaurant_id, payload)

@router.put("/{restaurant_id}/menu/bulk", response_model=list[MenuItem], dependencies=[Depends(check_manager)])
def bulk_update_menu_items_route(restaurant_id: int, payload: MenuItem_Bulk_Update):
    """
    **Updates multiple existing menu items for a given restaurant. Must be one of the restaurant managers to use.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to be updated
    *   **payload** (MenuItem_Bulk_Update): all modifications to existing items

    Returns:
    *   **list[MenuItem]**: a list of the newly updated menu items

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    return bulk_menu_item_update(restaurant_id, payload)

@router.post("/{restaurant_id}/menu", response_model=MenuItem, status_code=201, dependencies=[Depends(check_manager)])
def create_menu_item_route(restaurant_id: int, payload: MenuItem_Create):
    """
    **Creates a new menu item to add to restaurant's menu. Must be one of the restaurant managers to use.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant associated with the new item
    *   **payload** (MenuItem_Create): the new menu item details

    Returns:
    *   **MenuItem**: the newly created menu item

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    return create_menu_item(restaurant_id, payload)

@router.get("/{restaurant_id}/orders", response_model=list[Order])
def restaurant_orders_route(restaurant_id: int, current_user: User = Depends(check_manager)):
    """
    **Retrieves all orders for a particular restaurant. Must be one of the restaurant managers to use.**

    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to be updated
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.
    
    Returns:
    *   **list[Order]**: all orders for the given restaurant

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    return get_orders_for_restaurant(restaurant_id=restaurant_id, manager_id=current_user.id)

@router.put("/{restaurant_id}/menu/{menu_item_id}", response_model=MenuItem, dependencies=[Depends(check_manager)])
def update_menu_item_route(restaurant_id: int, menu_item_id: int, payload: MenuItem_Update):
    """
    **Updates a menu item in the restaurant's menu. Must be one of the restaurant managers to use.**

    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant to receive the updates
    *   **menu_item_id** (int): the identifier of the menu item to be updated
    *   **payload** (MenuItem_Update): the updated menu item details

    Returns:
    *   **MenuItem**: the updated menu item

    Raises:
    *   **HTTPException** (status_code = 400): restaurant_id in payload and URL do not match
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    if menu_item_id != payload.id:
        raise HTTPException(status_code=400, detail="Menu item ID in path and body must match")
    return update_menu_item(restaurant_id, payload)
