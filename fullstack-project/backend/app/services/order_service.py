""" This module implements business logic for order management. """

import datetime

from fastapi import HTTPException

from app.repositories.order_repo import load_orders, save_orders
from app.services.restaurant_service import get_restaurant_by_id, get_managers
from app.schemas.user_schema import Customer
from app.services.cart_service import empty_cart
from app.services.notification_service import Notification
from app.schemas.order_schema import Order
from app.schemas.receipt_schema import Receipt

async def create_order_from_receipt(current_user: Customer, receipt: Receipt) -> Order:
    """
    Converts the customer's cart into an order with a pre-saved receipt after sucessful payment
    Order details are taken from the receipt and once the order is saved cart is emptied

    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"
        receipt (Receipt): the save receipt containing the total pricing for the order

    Returns:
        Order: the newly created Order, which contains all details of the customer's order including receipt

    Raises:
        HTTPException (status_code = 400): if cart is empty
        HTTPException (status_code = 409): if generated id is the same as an existing id.
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
        "date_created": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    orders.append(new_order)
    save_orders(orders)
    empty_cart(current_user)

    await send_status_notification(new_order)

    return new_order

def get_orders_for_customer(current_customer: Customer) -> list[Order]:
    """
    Retrieves all orders in history that the provided customer has made.

    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        list[Order]: a list of all orders this customer has made
    """
    orders = load_orders()
    return [order for order in orders if order.get("customer_id") == current_customer.id]

def get_orders_for_restaurant(restaurant_id: int, manager_id: int) -> list[Order]:
    """
    Retrieves all orders in history that were/will be prepared by this restaurant.
    May only be accessed by a valid manager of the restaurant.

    Parameters:
        restaurant_id (int): the identifier of the restaurant whose orders are to be retrieved
        manager_id: the identifier of a valid manager of the restaurant

    Returns:
        list[Order]: a list of all orders associated with this restaurant

    Raises:
        HTTPException (status_code = 403): if provided manager_id is not in list of managers for this restaurant
        HTTPException (status_code = 404): restaurant_id not found in restaurants.json
    """
    restaurant = get_restaurant_by_id(restaurant_id)
    if manager_id not in restaurant.get("manager_ids", []):
        raise HTTPException(status_code=403, detail="Unauthorized to view orders for this restaurant.")
    
    orders = load_orders()
    return [order for order in orders if order.get("restaurant_id") == restaurant_id]

async def cancel_order(order_id: int, current_user: Customer) -> Order:
    """
    Cancels a pending order. Can only be cancelled by the customer that placed the order.

    Parameters:
        order_id (int): the identifier of the order to cancel
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        Order: the cancelled order
    
    Raises:
        HTTPException (status_code = 409): if current user's id does not match the order's customer id
        HTTPException (status_code = 400): if order has a status other than "pending"
        HTTPException (status_code = 404): if order is not found in orders.json
    """
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

async def update_order_status(order_id:int, new_status:str, manager_id:int) -> Order:
    """
    Accepts or declines a pending order for a restaurant which the provided manager manages.

    Parameters: 
        order_id (int): the identifier of the order receiving the status change
        new_status (str): the new status of the order (accepted or rejected)
        manager_id (str): the identifier of the manager who is performing the status change. Must be a manager of this order's restaurant.
    
    Returns:
        Order: the updated order with the status change

    Raises:
        HTTPException (status_code = 403): if provided manager_id is not in list of managers for this restaurant
        HTTPException (status_code = 400): if order has a status other than "pending"
        HTTPException (status_code = 404): if order is not found in orders.json, or order's restaurant id not found in restaurants.json
    """
    orders = load_orders()

    for order in orders:
        if order.get("id") == order_id:
            restaurant = get_restaurant_by_id(order.get("restaurant_id"))
            if manager_id not in restaurant.get("manager_ids",[]):
                raise HTTPException(status_code=403, detail = "You are not authorized to manage orders for this resturant")
            
            current_status = order.get("status")
            if current_status != "pending":
                raise HTTPException(status_code=400, detail=f"Order cannot be updated - current status is '{current_status}'.")
            
            order["status"] = new_status
            save_orders(orders)
            await send_status_notification(order)
            return Order(**order)

    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

async def send_status_notification(order: dict) -> None:
    """
    Sends a notification to the customer and restaurant managers when their associated order status changes.

    Parameters:
        order (dict): the associated order that requires a notification to be sent
    
    Returns: None
    """
    customer_id = order["customer_id"]
    restaurant_id = order["restaurant_id"]
    manager_ids = get_managers(restaurant_id)
    # TODO: add delivery driver id to notified users.
    notified_users = [customer_id] + manager_ids
    restaurant_name = get_restaurant_by_id(restaurant_id)["name"]
    notification = Notification(f"Order {order['id']} from {restaurant_name} set to status: {order['status']}", notified_users)
    await notification.send_to_users()
