"""
This module defines the API routes for delivery management.
Any updates to delivery routes should follow this module.
"""
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.delivery_schema import Delivery
from app.schemas.user_schema import User, UserRole
from app.auth import require_role, get_current_user
from app.services.delivery_service import (
    start_delivery,
    complete_delivery,
    get_delivery_by_order,
    check_waiting_orders,
)
from app.repositories.user_repo import load_users, save_users
from app.repositories.delivery_repo import load_deliveries

router = APIRouter(prefix="/delivery", tags=["delivery"])


@router.patch("/status", status_code=200)
async def update_driver_status_route(
    status: str,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    """
    **Allows a delivery driver to update their own availability status.**
    **If the driver sets their status to available, the system automatically checks for any waiting orders and assigns the oldest matching one.**

    Parameters:
    *   **status** (str): the new driver status. must be either *available* or *unavailable*
    *   **current_user** (User): the authenticated user with role *driver*. automatically passed as argument.

    Returns:
    *   **dict**: confirmation message with the updated status

    Raises:
    *   **HTTPException** (status_code = 400): if status is not *available* or *unavailable*
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *driver*
    """
    if status not in ("available", "unavailable"):
        raise HTTPException(status_code=400, detail="status can only be manually updated to one of available or unavailable")

    users = load_users()
    updated_user = None
    for user in users:
        if user.get("id") == current_user.id:
            user["driver_status"] = status
            updated_user = user
            break
    save_users(users)

    if status == "available" and updated_user:
        await check_waiting_orders(updated_user)

    return {"message": f"status updated to {status}"}


@router.get("/my-active", response_model=Delivery, status_code=200)
def get_my_active_delivery_route(
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    """
    **Returns the active (not yet completed) delivery assigned to the logged-in driver.**

    Parameters:
    *   **current_user** (User): the authenticated user with role *driver*. automatically passed as argument.

    Returns:
    *   **Delivery**: the active delivery for this driver

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *driver*
    *   **HTTPException** (status_code = 404): if no active delivery found for this driver
    """
    deliveries = load_deliveries()
    for delivery in deliveries:
        if delivery.get("driver_id") == current_user.id and delivery.get("delivered_at", 0.0) == 0.0:
            return Delivery(**delivery)
    raise HTTPException(status_code=404, detail="No active delivery found")


@router.patch("/{order_id}/start", response_model=Delivery, status_code=200)
async def start_delivery_route(
    order_id: int,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    """
    **Marks a delivery as started. Records the start time and calculates the ETA.**
    **Updates the associated order status from** *preparing* **to** *delivering.*

    Parameters:
    *   **order_id** (int): the identifier of the order being delivered
    *   **current_user** (User): the authenticated user with role *driver*. automatically passed as argument.

    Returns:
    *   **Delivery**: the updated delivery record

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *driver*, or driver is not assigned to this delivery
    *   **HTTPException** (status_code = 400): if delivery has already been started
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    return await start_delivery(order_id, current_user.id)


@router.patch("/{order_id}/complete", response_model=Delivery, status_code=200)
async def complete_delivery_route(
    order_id: int,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    """
    **Marks a delivery as completed. Records the delivered timestamp, actual delivery time, and delay.**
    **Also updates the associated order status to** *delivered* **and sets the driver back to available.**

    Parameters:
    *   **order_id** (int): the identifier of the order being completed
    *   **current_user** (User): the authenticated user with role *driver*. automatically passed as argument.

    Returns:
    *   **Delivery**: the completed delivery record

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *driver*, or driver is not assigned to this delivery
    *   **HTTPException** (status_code = 400): if delivery has not been started, or already completed
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    return await complete_delivery(order_id, current_user.id)


@router.get("/{order_id}", response_model=Delivery, status_code=200)
def get_delivery_by_order_route(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    **Retrieves the delivery record for a given order.**

    Parameters:
    *   **order_id** (int): the identifier of the order
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **Delivery**: the delivery record for this order

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    return get_delivery_by_order(order_id)