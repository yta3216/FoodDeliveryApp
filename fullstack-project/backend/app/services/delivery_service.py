import time
from fastapi import HTTPException
from app.repositories.delivery_repo import load_deliveries, save_deliveries
from app.repositories.user_repo import load_users, save_users
from app.schemas.delivery_schema import Delivery


BIKE_SPEED_KMH = 20.0
CAR_SPEED_KMH = 50.0
BIKE_MAX_DISTANCE_KM = 5.0


# figure out which vehicle is needed based on distance
def get_required_vehicle(distance_km: float) -> str:
    return "bike" if distance_km <= BIKE_MAX_DISTANCE_KM else "car"


# calculate eta in minutes based on distance and vehicle
def calculate_eta(distance_km: float, vehicle: str) -> float:
    speed = BIKE_SPEED_KMH if vehicle == "bike" else CAR_SPEED_KMH
    return round((distance_km / speed) * 60, 2)


# find the best available driver for this order based on vehicle and availability
# returns the driver dict or None if no driver is available
def find_available_driver(required_vehicle: str) -> dict | None:
    users = load_users()
    candidates = [
        u for u in users
        if u.get("role") == "driver"
        and u.get("driver_status") == "available"
        and u.get("vehicle") == required_vehicle
    ]
    if not candidates:
        return None
    # pick the one who has been available the longest: we use id as tiebreaker
    # in a real system we'd track available_since timestamp but for now lowest id = longest tenured
    return candidates[0]


# assign a driver to an order, update driver status to delivering
def assign_driver_to_order(driver_id: str) -> None:
    users = load_users()
    for user in users:
        if user.get("id") == driver_id:
            user["driver_status"] = "delivering"
            break
    save_users(users)


# create a delivery record when a driver is assigned
def create_delivery(order_id: int, driver_id: str, distance_km: float) -> Delivery:
    vehicle = get_required_vehicle(distance_km)
    deliveries = load_deliveries()
    new_id = max((d.get("id", 0) for d in deliveries), default=0) + 1

    new_delivery = {
        "id": new_id,
        "order_id": order_id,
        "driver_id": driver_id,
        "method": vehicle,
        "distance_km": distance_km,
        "eta_minutes": 0.0,     # calculated when driver marks delivering
        "started_at": 0.0,      # set when driver marks delivering
        "delivered_at": 0.0,
        "actual_minutes": 0.0,
    }

    deliveries.append(new_delivery)
    save_deliveries(deliveries)
    return Delivery(**new_delivery)


# called when driver marks order as delivering: starts the timer and calculates eta
def start_delivery(order_id: int, driver_id: str) -> Delivery:
    from app.repositories.order_repo import load_orders, save_orders
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
            delivery["eta_minutes"] = calculate_eta(distance_km, vehicle)
            save_deliveries(deliveries)

            # flip order status from preparing to delivering
            orders = load_orders()
            for order in orders:
                if order.get("id") == order_id:
                    order["status"] = "delivering"
                    break
            save_orders(orders)

            return Delivery(**delivery)

    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")

# called when driver marks order as delivered: stops the timer and records actual time
def complete_delivery(order_id: int, driver_id: str) -> Delivery:
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
            # positive = late, negative = early
            delivery["delay_minutes"] = round(actual_minutes - delivery.get("eta_minutes", 0.0), 2)
            save_deliveries(deliveries)

            # set driver status back to available
            users = load_users()
            for user in users:
                if user.get("id") == driver_id:
                    user["driver_status"] = "available"
                    break
            save_users(users)

            return Delivery(**delivery)

    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")

# get delivery info for a specific order — for customer to view
def get_delivery_by_order(order_id: int) -> Delivery:
    deliveries = load_deliveries()
    for delivery in deliveries:
        if delivery.get("order_id") == order_id:
            return Delivery(**delivery)
    raise HTTPException(status_code=404, detail=f"Delivery for order '{order_id}' not found.")


# called when a driver sets their status to available —
# checks if any orders are waiting for a driver and assigns the oldest one
def check_waiting_orders(driver: dict) -> None:
    from app.repositories.order_repo import load_orders, save_orders
    orders = load_orders()
    required_vehicle = driver.get("vehicle")

    # find orders waiting for a driver that match this vehicle type
    waiting = [
        o for o in orders
        if o.get("status") == "waiting_for_driver"
        and get_required_vehicle(o.get("distance_km", 0.0)) == required_vehicle
    ]

    if not waiting:
        return

    # assign the oldest waiting order (lowest id = placed first)
    waiting.sort(key=lambda o: o["id"])
    order = waiting[0]

    # create delivery and update order
    delivery = create_delivery(order["id"], driver["id"], order.get("distance_km", 0.0))
    assign_driver_to_order(driver["id"])

    for o in orders:
        if o["id"] == order["id"]:
            o["status"] = "delivering"
            o["delivery_id"] = delivery.id
            break
    save_orders(orders)