""" This module implements business logic for order management. """

import datetime

from fastapi import HTTPException

from app.repositories.order_repo import load_orders, save_orders
from app.services.restaurant_service import get_restaurant_by_id, get_managers
from app.schemas.user_schema import Customer
from app.services.cart_service import calculate_cart_total, empty_cart, get_cart
from app.services.notification_service import Notification
from app.schemas.order_schema import Order, OrderItemsUpdate, OrderCreate

async def create_order_from_cart(current_user: Customer, payload: OrderCreate) -> Order:
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
        "distance_km": payload.distance_km,
        "delivery_fee": 0.0,
        "tax": 0.0,
        "subtotal": calculate_cart_total(cart),
        "date_created": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    orders.append(new_order)
    save_orders(orders)
    empty_cart(current_user)

    await send_status_notification(new_order)

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
async def cancel_order(order_id: int, current_user: Customer) -> Order:
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            if order.get("customer_id") != current_user.id:
                raise HTTPException(status_code=403, detail= "Your are not authorized to cancel this order.")
            if order.get("status") != "pending":
                raise HTTPException(status_code=400, detail= f"Order cannot be cancelled, order is already '{order.get('status')}'.")
            order["status"] = "cancelled"
            save_orders(orders)
            await send_status_notification(order)
            return Order(**order)
        
    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

# Manager accepts or declines pending order
# if accepted, tries to assign a driver: if none available, order goes to waiting_for_driver
async def update_order_status(order_id: int, new_status: str, manager_id: int) -> Order:
    from app.services.delivery_service import (
        create_delivery, assign_driver_to_order, find_available_driver, get_required_vehicle
    )
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            restaurant = get_restaurant_by_id(order.get("restaurant_id"))
            if manager_id not in restaurant.get("manager_ids",[]):
                raise HTTPException(status_code=403, detail = "You are not authorized to manage orders for this resturant")
            
            current_status = order.get("status")
            if current_status != "pending":
                raise HTTPException(status_code=400, detail=f"Order cannot be updated - current status is '{current_status}'.")

            if new_status == "rejected":
                order["status"] = "rejected"
                save_orders(orders)
                await send_status_notification(order)
                return Order(**order)

            # manager accepted: try to assign a driver
            distance_km = order.get("distance_km", 0.0)
            required_vehicle = get_required_vehicle(distance_km)
            driver = find_available_driver(required_vehicle)

            if driver:
                # driver found: create delivery and set to preparing
                delivery = create_delivery(order_id, driver["id"], distance_km)
                assign_driver_to_order(driver["id"])
                order["status"] = "preparing"
                order["delivery_id"] = delivery.id
            else:
                # no driver available: wait in queue
                order["status"] = "waiting_for_driver"

            save_orders(orders)
            await send_status_notification(order)
            return Order(**order)

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

# update items on a pending order: blocked if the order is already confirmed
def update_order_items(order_id: int, payload: OrderItemsUpdate, current_user: Customer) -> Order:
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            # make sure this order belongs to the customer making the request
            if order.get("customer_id") != current_user.id:
                raise HTTPException(status_code=403, detail="You are not authorized to edit this order.")

            # block edits once the order is no longer pending
            if order.get("status") != "pending":
                raise HTTPException(status_code=400, detail=f"Order is locked and cannot be edited — current status is '{order.get('status')}'.")

            # replace the items list with what the customer sent
            order["items"] = [{"menu_item_id": item.menu_item_id, "qty": item.qty} for item in payload.items]
            save_orders(orders)
            return Order(**order)

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

# send order status update notification
async def send_status_notification(order: dict) -> None:
    customer_id = order["customer_id"]
    restaurant_id = order["restaurant_id"]
    manager_ids = get_managers(restaurant_id)
    # TODO: add delivery driver id to notified users.
    notified_users = [customer_id] + manager_ids
    restaurant_name = get_restaurant_by_id(restaurant_id)["name"]
    notification = Notification(f"Order {order['id']} from {restaurant_name} set to status: {order['status']}", notified_users)
    await notification.send_to_users()