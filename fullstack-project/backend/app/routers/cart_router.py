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
    empty_cart,
    create_cart_item,
    update_cart_item,
    delete_cart_item,
)

router = APIRouter(prefix="/cart", tags=["cart"])

# put request to update cart restaurant ID. new restaurant id must exist
@router.put("/{restaurant_id}", response_model=Cart, dependencies=[Depends(get_restaurant_by_id)])
def update_cart_restaurant_route(restaurant_id: int, customer: Customer = Depends(get_customer)):
    return update_cart_restaurant(restaurant_id, customer)

# delete request to empty the cart.
@router.delete("", status_code=204)
def empty_cart_route(customer: Customer = Depends(get_customer)):
    return empty_cart(customer)

# post request to add an item to cart
@router.post("/item", response_model=CartItem, status_code=201)
def create_cart_item_route(payload: CartItem_Create, customer: Customer = Depends(get_customer)):
    return create_cart_item(payload, customer)

# put request to update qty of an item in cart
@router.put("/item/{item_id}", response_model=CartItem)
def update_cart_item_route(item_id: int, payload: CartItem_Update, customer: Customer = Depends(get_customer)):
    return update_cart_item(item_id, payload, customer)

# delete request to remove an item from cart. status code is 200 because it returns the removed item.
@router.delete("/item/{item_id}", response_model=CartItem, status_code=200)
def delete_cart_item(item_id: int, customer = Depends(get_customer)):
    return delete_cart_item(item_id, customer)
