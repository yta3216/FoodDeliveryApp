"""
This module defines the API routes for restaurant management.
Functions use get_cart as a dependency, which will authenticate
the user, verify they are a customer, and return their cart.
"""

from fastapi import APIRouter, Depends

from app.schemas.user_schema import Customer
from app.services.user_service import get_customer
from app.services.restaurant_service import get_restaurant_by_id
from app.schemas.cart_schema import (
    CartItem,
    CartItem_Create,
    CartItem_Update,
    Cart,
)
from app.services.cart_service import (
    update_cart_restaurant,
    get_cart,
    empty_cart,
    create_cart_item,
    get_cart_item,
    update_cart_item,
    delete_cart_item,
)

router = APIRouter(prefix="/cart", tags=["cart"])

@router.patch("/{restaurant_id}", response_model=Cart, dependencies=[Depends(get_restaurant_by_id)])
def update_cart_restaurant_route(restaurant_id: int, customer: Customer = Depends(get_customer)):
    """
    **Updates the restaurant associated with a user's cart, used when they want to change the restaurant they're ordering from.  
    The cart is emptied if the new restaurant is different than the old one, as the items are no longer applicable.**

    Parameters:
    *   **restaurant_id** (int): the new restaurant id for customer's cart
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.
    
    Returns:
    *   **Cart**: the updated cart

    Raises:
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current_user's user_id not found in users.json
    """
    return update_cart_restaurant(restaurant_id, customer)

@router.get("", response_model=Cart)
def get_cart_route(customer: Customer = Depends(get_customer)):
    """
    **Retrieves a logged-in customers cart.**
    
    Parameters:
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **Cart**: the customer's cart

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current_user's user_id not found in users.json
    """
    return get_cart(customer)

@router.delete("", status_code=204)
def empty_cart_route(customer: Customer = Depends(get_customer)):
    """
    **Empties the contents of a logged-in customer's cart.**
    
    Parameters:
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.
    
    Returns: None

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current_user's user_id not found in users.json
    """
    return empty_cart(customer)

@router.post("/item", response_model=CartItem, status_code=201)
def create_cart_item_route(payload: CartItem_Create, customer: Customer = Depends(get_customer)):
    """
    **Adds an item to a logged-in in customer's cart.**
    
    Parameters:
    *   **payload** (CartItem_Create): details of the new cart item
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **CartItem**: the new cart item

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 400): if user's cart has no associated restaurant
    *   **HTTPException** (status_code = 404):
        *   current user's cart's restaurant_id not found in restaurants.json
        *   current user's id not found in users.json
        *   new cart item's id not found in restaurant's menu
    """
    return create_cart_item(payload, customer)

@router.get("/item/{item_id}", response_model=CartItem)
def get_cart_item_route(item_id: int, customer: Customer = Depends(get_customer)):
    """
    **Retrieves an item from a logged-in customer's cart.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be retrieved
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **CartItem**: the requested cart item

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    return get_cart_item(item_id, customer)

@router.patch("/item/{item_id}", response_model=CartItem)
def update_cart_item_route(item_id: int, payload: CartItem_Update, customer: Customer = Depends(get_customer)):
    """
    **Updates the quantity of an item in a logged-in customer's cart.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be updated
    *   **payload** (CartItem_Update): the details of the item update
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **CartItem**: the updated cart item

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    return update_cart_item(item_id, payload, customer)

@router.delete("/item/{item_id}", response_model=CartItem, status_code=200)
def delete_cart_item_route(item_id: int, customer = Depends(get_customer)):
    """
    **Removes an item from a logged-in customer's cart and returns it.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be retrieved
    *   **customer** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **CartItem**: the deleted cart item

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    return delete_cart_item(item_id, customer)
