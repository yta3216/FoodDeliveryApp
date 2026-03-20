"""
This module implements business logic for delivery assignment and tracking.
Bikes are used for orders within 5km (20km/h), cars for longer distances (50km/h).
ETA is calculated when the driver marks the order as delivering.
Any updates to delivery logic should follow this module.
"""

import time
from fastapi import HTTPException
from app.repositories.delivery_repo import load_deliveries, save_deliveries
from app.repositories.user_repo import load_users, save_users
from app.services.order_service import send_status_notification
from app.services.restaurant_service import get_restaurant_by_id
from app.repositories.order_repo import load_orders, save_orders
from app.services.notification_service import Notification
from app.schemas.delivery_schema import Delivery


BIKE_SPEED_KMH = 20.0
CAR_SPEED_KMH = 50.0
BIKE_MAX_DISTANCE_KM = 5.0


def get_required_vehicle(distance_km: float) -> str:
    """
    Determines which vehicle type is required based on delivery distance.
    Orders within 5km use a bike, longer distances require a car.

    Parameters:
        distance_km (float): the delivery distance in kilometres

    Returns:
        str: "bike" or "car"
    """
    return "bike" if distance_km <= BIKE_MAX_DISTANCE_KM else "car"


def calculate_eta(distance_km: float, vehicle: str) -> float:
    """
    Calculates the estimated delivery time in minutes based on distance and vehicle type.

    Parameters:
        distance_km (float): the delivery distance in kilometres
        vehicle (str): the vehicle type, either "bike" or "car"

    Returns:
        float: estimated delivery time in minutes, rounded to 2 decimal places
    """
    speed = BIKE_SPEED_KMH if vehicle == "bike" else CAR_SPEED_KMH
    return round((distance_km / speed) * 60, 2)


def find_available_driver(required_vehicle: str) -> dict | None:
    """
    Finds the best available driver for an order based on vehicle type.
    Picks the first available driver with the matching vehicle type as a tiebreaker.

    Parameters:
        required_vehicle (str): the vehicle type required for this order, either "bike" or "car"

    Returns:
        dict | None: the driver user dict if one is available, otherwise None
    """
    users = load_users()
    candidates = [
        u for u in users
        if u.get("role") == "driver"
        and u.get("driver_status") == "available"
        and u.get("vehicle") == required_vehicle
    ]
    if not candidates:
        return None
    return candidates[0]


def set_driver_status_to_delivering(driver_id: str) -> None:
    """
    Updates a driver's status to "delivering" when they are assigned an order.

    Parameters:
        driver_id (str): the identifier of the driver to update

    Returns:
        None
    """
    users = load_users()
    for user in users:
        if user.get("id") == driver_id:
            user["driver_status"] = "delivering"
            break
    save_users(users)


def create_delivery(order_id: int, driver_id: str, distance_km: float) -> Delivery:
    """
    Creates a new delivery record when a driver is assigned to an order.
    ETA and timing fields are set to 0 until the driver marks the delivery as started.

    Parameters:
        order_id (int): the identifier of the order being delivered
        driver_id (str): the identifier of the assigned driver
        distance_km (float): the delivery distance in kilometres

    Returns:
        Delivery: the newly created delivery record
    """
    vehicle = get_required_vehicle(distance_km)
    deliveries = load_deliveries()
    new_id = max((d.get("id", 0) for d in deliveries), default=0) + 1

    new_delivery = {
        "id": new_id,
        "order_id": order_id,
        "driver_id": driver_id,
        "method": vehicle,
        "distance_km": distance_km,
        "eta_minutes": 0.0,
        "started_at": 0.0,
        "delivered_at": 0.0,
        "actual_minutes": 0.0,
        "delay_minutes": 0.0,
    }

    deliveries.append(new_delivery)
    save_deliveries(deliveries)
    return Delivery(**new_delivery)


async def start_delivery(order_id: int, driver_id: str) -> Delivery:
    """
    Marks a delivery as started, records the start timestamp, and calculates the ETA.
    Also updates the associated order status from "preparing" to "delivering".

    Parameters:
        order_id (int): the identifier of the order being delivered
        driver_id (str): the identifier of the driver starting the delivery

    Returns:
        Delivery: the updated delivery record with eta_minutes and started_at populated

    Raises:
        HTTPException (status_code = 403): if the driver is not assigned to this delivery
        HTTPException (status_code = 400): if the delivery has already been started
        HTTPException (status_code = 404): if no delivery record is found for this order
    """
    deliveries = load_deliveries()
    for delivery in deliveries:
        if delivery.get("order_id") == order_id:
            if delivery.get("driver_id") != driver_id:
                raise HTTPException(status_code=403, detail="You are not assigned to this delivery.")
            if delivery.get("started_at") != 0.0:
                raise HTTPException(status_code=400, detail="Delivery already started.")

            now = time.time()
            vehicle = delivery.get("method")
            distance_km = delivery.get("distance_km")
            delivery["started_at"] = now
            eta = calculate_eta(distance_km, vehicle)
            delivery["eta_minutes"] = eta
            save_deliveries(deliveries)

            orders = load_orders()
            for order in orders:
                if order.get("id") == order_id:
                    order["status"] = "delivering"
                    await send_new_delivery_notification(delivery)
                    break
            save_orders(orders)

            return Delivery(**delivery)

    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")


def complete_delivery(order_id: int, driver_id: str) -> Delivery:
    """
    Marks a delivery as completed, records the delivered timestamp and actual delivery time.
    Calculates delay_minutes as the difference between actual and estimated time.
    Also sets the driver's status back to "available".

    Parameters:
        order_id (int): the identifier of the order being completed
        driver_id (str): the identifier of the driver completing the delivery

    Returns:
        Delivery: the completed delivery record with all timing fields populated

    Raises:
        HTTPException (status_code = 403): if the driver is not assigned to this delivery
        HTTPException (status_code = 400): if the delivery has not been started yet
        HTTPException (status_code = 400): if the delivery has already been completed
        HTTPException (status_code = 404): if no delivery record is found for this order
    """
    deliveries = load_deliveries()
    for delivery in deliveries:
        if delivery.get("order_id") == order_id:
            if delivery.get("driver_id") != driver_id:
                raise HTTPException(status_code=403, detail="You are not assigned to this delivery.")
            if delivery.get("started_at") == 0.0:
                raise HTTPException(status_code=400, detail="Delivery has not started yet.")
            if delivery.get("delivered_at") != 0.0:
                raise HTTPException(status_code=400, detail="Delivery already completed.")

            now = time.time()
            actual_minutes = round((now - delivery["started_at"]) / 60, 2)
            delivery["delivered_at"] = now
            delivery["actual_minutes"] = actual_minutes
            delivery["delay_minutes"] = round(actual_minutes - delivery.get("eta_minutes", 0.0), 2)
            save_deliveries(deliveries)

            users = load_users()
            for user in users:
                if user.get("id") == driver_id:
                    user["driver_status"] = "available"
                    break
            save_users(users)

            return Delivery(**delivery)

    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")


def get_delivery_by_order(order_id: int) -> Delivery:
    """
    Retrieves the delivery record associated with a given order.

    Parameters:
        order_id (int): the identifier of the order

    Returns:
        Delivery: the delivery record for this order

    Raises:
        HTTPException (status_code = 404): if no delivery record is found for this order
    """
    deliveries = load_deliveries()
    for delivery in deliveries:
        if delivery.get("order_id") == order_id:
            return Delivery(**delivery)
    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")


def check_waiting_orders(driver: dict) -> None:
    """
    Called when a driver sets their status to available.
    Checks if any orders are waiting for a driver with the matching vehicle type,
    and assigns the oldest waiting order to this driver.

    Parameters:
        driver (dict): the driver user dict, must include "vehicle" and "id" fields

    Returns:
        None
    """
    orders = load_orders()
    required_vehicle = driver.get("vehicle")

    waiting = [
        o for o in orders
        if o.get("status") == "waiting_for_driver"
        and get_required_vehicle(o.get("distance_km", 0.0)) == required_vehicle
    ]

    if not waiting:
        return

    waiting.sort(key=lambda o: o["id"])
    order = waiting[0]

    delivery = create_delivery(order["id"], driver["id"], order.get("distance_km", 0.0))
    set_driver_status_to_delivering(driver["id"])

    for o in orders:
        if o["id"] == order["id"]:
            o["status"] = "preparing"
            o["delivery_id"] = delivery.id
            break
    save_orders(orders)

async def send_new_delivery_notification(delivery: dict, eta: float):
    """
    Sends a notification to the customer that order has been set to delivering status,
    and another to notify them of delivery eta and transportation method.

    Parameters:
        delivery (dict): the delivery that triggered the notification
        eta (float): the eta for this order

    Returns: None

    Raises:
        HTTPException(status_code=400): if notification does not have any recipients
    """
    order_id = delivery.get("order_id")
    orders = load_orders()
    for order in orders:
        if order.get("id") == order_id:
            order = order

    await send_status_notification(order)

    customer_id = order["customer_id"]
    restaurant_id = order["restaurant_id"]
    restaurant_name = get_restaurant_by_id(restaurant_id)["name"]
    vehicle = delivery["method"]
    notification = Notification(
        f"Order {order['id']} from {restaurant_name} will arrive in approximately "
        f"{eta} minutes via {vehicle}.", [customer_id])
    await notification.send_to_users()
