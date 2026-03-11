""" This module implements business logic for order management. """

import datetime

from fastapi import HTTPException

from app.repositories.order_repo import load_orders, save_orders
from app.services.restaurant_service import get_restaurant_by_id
from app.schemas.user_schema import Customer
from app.services.cart_service import calculate_cart_total, empty_cart, get_cart
from app.schemas.order_schema import Order

def create_order_from_cart(current_user: Customer) -> Order:
    cart = get_cart(current_user)
    if cart.restaurant_id == 0:
        raise HTTPException(status_code=400, detail="Cart is empty.")
    
    orders = load_orders()
    new_id = max((order.get("id", 0) for order in orders), default=0) + 1
    if any(order.get("id") == new_id for order in orders):
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    
    new_order = {
        "id": new_id,
        "customer_id": current_user.id,
        "restaurant_id": cart.restaurant_id,
        "delivery_id": 0,
        "items": [{
            "menu_item_id": item.menu_item_id,
            "qty": item.qty
        } for item in cart.cart_items],
        "status": "pending",
        "delivery_fee": 0.0,
        "tax": 0.0,
        "subtotal": calculate_cart_total(cart),
        "date_created": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    orders.append(new_order)
    save_orders(orders)
    empty_cart(current_user)

    return new_order

def get_orders_for_customer(current_customer: Customer) -> list[Order]:
    orders = load_orders()
    return [order for order in orders if order.get("customer_id") == current_customer.id]

def get_orders_for_restaurant(restaurant_id: int, manager_id: int) -> list[Order]:
    restaurant = get_restaurant_by_id(restaurant_id)
    if manager_id not in restaurant.get("manager_ids", []):
        raise HTTPException(status_code=403, detail="Unauthorized to view orders for this restaurant.")
    
    orders = load_orders()
    return [order for order in orders if order.get("restaurant_id") == restaurant_id]

# Cancel a pending order. Can be cancelled only by the customer that placed the order
# Cancelled orders are removed from orders.json
def cancel_order(order_id: int, current_user: Customer) -> None:
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            if order.get("customer_id") != current_user.id:
                raise HTTPException(status_code=403, detail= "Your are not authroized to cancel this order.")
            if order.get("status") != "pending":
                raise HTTPException(status_code=400, detail= f"Order cannot be cancelled, order is already '{order.get('status')}'.")
            orders.remove(order)
            save_orders(order)
            return
        
    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")
    
