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

@router.put("/{restaurant_id}", response_model=Cart, dependencies=[Depends(get_restaurant_by_id)])
def update_cart_restaurant_route(restaurant_id: int, customer: Customer = Depends(get_customer)):
    """
    **Updates the restaurant id associated with a logged-in customer's cart.**
    
    Parameters:
    *   **restaurant_id** (int): the new restaurant id for customer's cart
    
    Returns:
    *   **Cart**: the updated cart
    """
    return update_cart_restaurant(restaurant_id, customer)

@router.get("", response_model=Cart)
def get_cart_route(customer: Customer = Depends(get_customer)):
    """
    **Retrieves a logged-in customers cart.**
    
    Parameters: None

    Returns:
    *   **Cart**: the customer's cart
    """
    return get_cart(customer)

@router.delete("", status_code=204)
def empty_cart_route(customer: Customer = Depends(get_customer)):
    """
    **Empties the contents of a logged-in customer's cart.**
    
    Parameters: None
    
    Returns: None
    """
    return empty_cart(customer)

@router.post("/item", response_model=CartItem, status_code=201)
def create_cart_item_route(payload: CartItem_Create, customer: Customer = Depends(get_customer)):
    """
    **Adds an item to a logged-in in customer's cart.**
    
    Parameters:
    *   **payload** (CartItem_Create): details of the new cart item

    Returns:
    *   **CartItem**: the new cart item
    """
    return create_cart_item(payload, customer)

@router.get("/item/{item_id}", response_model=CartItem)
def get_cart_item_route(item_id: int, customer: Customer = Depends(get_customer)):
    """
    **Retrieves an item from a logged-in customer's cart.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be retrieved

    Returns:
    *   **CartItem**: the requested cart item
    """
    return get_cart_item(item_id, customer)

@router.put("/item/{item_id}", response_model=CartItem)
def update_cart_item_route(item_id: int, payload: CartItem_Update, customer: Customer = Depends(get_customer)):
    """
    **Updates the quantity of an item in a logged-in customer's cart.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be updated
    *   **payload** (CartItem_Update): the details of the item update

    Returns:
    *   **CartItem**: the updated cart item
    """
    return update_cart_item(item_id, payload, customer)

@router.delete("/item/{item_id}", response_model=CartItem, status_code=200)
def delete_cart_item(item_id: int, customer = Depends(get_customer)):
    """
    **Removes an item from a logged-in customer's cart and returns it.**
    
    Parameters:
    *   **item_id** (int): the identifier of the item to be retrieved

    Returns:
    *   **CartItem**: the deleted cart item
    """
    return delete_cart_item(item_id, customer)
