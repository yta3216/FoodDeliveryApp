""" This module implements business logic for order management. """

from fastapi import HTTPException

from app.repositories.user_repo import load_users, save_users
from app.repositories.order_repo import load_orders, save_orders
from app.services.restaurant_service import get_restaurant_by_id
from app.schemas.user_schema import Customer
from app.schemas.cart_schema import (
    CartItem,
    CartItem_Update,
    CartItem_Create,
    Cart
)
from app.services.cart_service import calculate_cart_total, get_cart, get_cart_item
from app.schemas.order_schema import (
    Order,
    OrderItem,
    OrderItem_Create,
    OrderItem_Update,
)

def create_order_from_cart(current_user: Customer) -> Order:
    orders = load_orders()
    new_id = max((order.get("id", 0) for order in orders), default=0) + 1 # generate unique ID for the new order
    if any(order.get("id") == new_id for order in orders):
        raise HTTPException(status_code=409, detail="ID collision; retry.") # just in case, though should not be possible
    
    cart = get_cart(current_user)
    if cart.restaurant_id == 0:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    new_order = {
        "id": new_id,
        "customer_id": current_user.id,
        "restaurant_id": cart.restaurant_id,
        "delivery_id": None,
        "items": [{
            "menu_item_id": item.menu_item_id,
            "qty": item.qty
        } for item in cart.cart_items],
        "status": "pending",
        "delivery_fee": 0.0,
        "tax": 0.0,
        "total_price": calculate_cart_total(cart)
    }