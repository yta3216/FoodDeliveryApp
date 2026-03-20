"""
This module implements business logic for order management.
Any updates to order logic should follow this module.
"""

import datetime

from fastapi import HTTPException

from app.repositories.order_repo import load_orders, save_orders
from app.services.restaurant_service import get_restaurant_by_id, get_managers
from app.schemas.user_schema import Customer
from app.services.cart_service import empty_cart
from app.services.notification_service import Notification
from app.schemas.order_schema import Order
from app.schemas.receipt_schema import Receipt
from app.services.receipt_service import get_receipt


async def create_order_from_receipt(current_user: Customer, receipt: Receipt) -> Order:
    """
    Converts a receipt into a pending order after successful payment.
    Pricing and item details are stored in the receipt — the order only references the receipt id.
    Cart is emptied once the order is saved.

    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"
        receipt (Receipt): the saved receipt associated with this order

    Returns:
        Order: the newly created order

    Raises:
        HTTPException (status_code = 409): if generated id collides with an existing order id
    """
    orders = load_orders()
    new_id = max((order.get("id", 0) for order in orders), default=0) + 1
    if any(order.get("id") == new_id for order in orders):
        raise HTTPException(status_code=409, detail="ID collision; retry.")

    new_order = {
        "id": new_id,
        "customer_id": current_user.id,
        "restaurant_id": receipt.restaurant_id,
        "delivery_id": 0,
        "receipt_id": receipt.id,
        "status": "pending",
        "distance_km": receipt.distance_km,
        "date_created": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    orders.append(new_order)
    save_orders(orders)
    empty_cart(current_user)

    await send_status_notification(new_order)

    return new_order


def get_orders_for_customer(current_customer: Customer) -> list[Order]:
    """
    Retrieves all orders placed by the provided customer.

    Parameters:
        current_customer (Customer): the current logged-in user. must have role "customer"

    Returns:
        list[Order]: a list of all orders this customer has placed
    """
    orders = load_orders()
    return [order for order in orders if order.get("customer_id") == current_customer.id]


def get_orders_for_restaurant(restaurant_id: int, manager_id: int) -> list[Order]:
    """
    Retrieves all orders associated with a restaurant.
    May only be accessed by a valid manager of that restaurant.

    Parameters:
        restaurant_id (int): the identifier of the restaurant
        manager_id (str): the identifier of the manager making the request

    Returns:
        list[Order]: a list of all orders for this restaurant

    Raises:
        HTTPException (status_code = 403): if the manager is not associated with this restaurant
        HTTPException (status_code = 404): if restaurant_id is not found
    """
    restaurant = get_restaurant_by_id(restaurant_id)
    if manager_id not in restaurant.get("manager_ids", []):
        raise HTTPException(status_code=403, detail="Unauthorized to view orders for this restaurant.")

    orders = load_orders()
    return [order for order in orders if order.get("restaurant_id") == restaurant_id]


async def cancel_order(order_id: int, current_user: Customer) -> Order:
    """
    Cancels a pending order. Only the customer who placed the order may cancel it.
    Sends a refund notification to the customer after cancellation.

    Parameters:
        order_id (int): the identifier of the order to cancel
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        Order: the cancelled order

    Raises:
        HTTPException (status_code = 403): if the current user did not place this order
        HTTPException (status_code = 400): if the order status is not "pending"
        HTTPException (status_code = 404): if the order is not found
    """
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            if order.get("customer_id") != current_user.id:
                raise HTTPException(status_code=403, detail="You are not authorized to cancel this order.")
            if order.get("status") != "pending":
                raise HTTPException(status_code=400, detail=f"Order cannot be cancelled, order is already '{order.get('status')}'.")
            order["status"] = "cancelled"
            save_orders(orders)
            await send_status_notification(order)
            receipt = get_receipt(order["receipt_id"])
            send_refund_notification(order, "Order cancelled by customer")
            return Order(**order)

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")


async def accept_reject_order(order_id: int, new_status: str, manager_id: int) -> Order:
    """
    Accepts or rejects a pending order for a restaurant which the provided manager manages.
    If accepted and the order is within the delivery radius, a driver is assigned if available.
    If no driver is available, the order goes to waiting_for_driver status.
    If the order is outside the restaurant's delivery radius, it is automatically rejected.
    Sends a refund notification to the customer when an order is rejected.

    Parameters:
        order_id (int): the identifier of the order receiving the status change
        new_status (str): the requested new status. must be "accepted" or "rejected"
        manager_id (str): the identifier of the manager making the request. must manage this order's restaurant

    Returns:
        Order: the updated order

    Raises:
        HTTPException (status_code = 403): if the manager does not manage this order's restaurant
        HTTPException (status_code = 400): if the order status is not "pending"
        HTTPException (status_code = 404): if the order or restaurant is not found
    """
    from app.services.delivery_service import (
        create_delivery, set_driver_status_to_delivering, find_available_driver, get_required_vehicle
    )
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            restaurant = get_restaurant_by_id(order.get("restaurant_id"))
            if manager_id not in restaurant.get("manager_ids", []):
                raise HTTPException(status_code=403, detail="You are not authorized to manage orders for this restaurant.")

            current_status = order.get("status")
            if current_status != "pending":
                raise HTTPException(status_code=400, detail=f"Order cannot be updated - current status is '{current_status}'.")

            if new_status == "rejected":
                order["status"] = "rejected"
                save_orders(orders)
                await send_status_notification(order)
                receipt = get_receipt(order["receipt_id"])
                send_refund_notification(order, f"Rejected by restaurant")
                return Order(**order)

            distance_km = order.get("distance_km", 0.0)
            delivery_radius = restaurant.get("max_delivery_radius_km", 0.0)
            if delivery_radius > 0 and distance_km > delivery_radius:
                order["status"] = "rejected"
                save_orders(orders)
                await send_status_notification(order)
                receipt = get_receipt(order["receipt_id"])
                refund_notification = Notification(
                    f"Refund of ${receipt.total} for order {order['id']} from {restaurant['name']} is being processed.",
                    [order["customer_id"]]
                )
                await refund_notification.send_to_users()
                return Order(**order)

            required_vehicle = get_required_vehicle(distance_km)
            driver = find_available_driver(required_vehicle)

            if driver:
                delivery = create_delivery(order_id, driver["id"], distance_km)
                set_driver_status_to_delivering(driver["id"])
                order["status"] = "preparing"
                order["delivery_id"] = delivery.id
            else:
                order["status"] = "waiting_for_driver"

            save_orders(orders)
            await send_status_notification(order)
            return Order(**order)

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")


async def send_status_notification(order: dict) -> None:
    """
    Sends a notification to the customer and restaurant managers when an order's status changes.

    Parameters:
        order (dict): the order that triggered the notification

    Returns:
        None
    """
    customer_id = order["customer_id"]
    restaurant_id = order["restaurant_id"]
    manager_ids = get_managers(restaurant_id)
    notified_users = [customer_id] + manager_ids
    restaurant_name = get_restaurant_by_id(restaurant_id)["name"]
    notification = Notification(f"Order {order['id']} from {restaurant_name} set to status: {order['status']}", notified_users)
    await notification.send_to_users()

async def send_refund_notification(order: dict, reason: str = None) -> None:
    """
    Sends a notification to the customer regarding a refund which was issued.

    Parameters:
        order (dict): the order which was refunded
        reason (str): the reason the order was refunded (optional)

    Returns:
        None
    """
    customer_id = order["customer_id"]
    order_id = order['id']
    restaurant_id = order["restaurant_id"]
    receipt = get_receipt(order["receipt_id"])
    notified_users = [customer_id]
    restaurant_name = get_restaurant_by_id(restaurant_id)["name"]

    message = f"Refund of ${receipt.total} for order {order_id} from {restaurant_name} is being processed."
    if reason:
        message += f" Reason: {reason}."

    notification = Notification(message, notified_users)
    await notification.send_to_users()