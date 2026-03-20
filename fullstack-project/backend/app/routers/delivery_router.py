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

router = APIRouter(prefix="/delivery", tags=["delivery"])


@router.patch("/status", status_code=200)
def update_driver_status_route(
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
        check_waiting_orders(updated_user)

    return {"message": f"status updated to {status}"}


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
    *   **Delivery**: the updated delivery record with eta_minutes and started_at populated

    Raises:
    *   **HTTPException** (status_code = 400): if delivery has already been started
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user is not the assigned driver for this delivery
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    return await start_delivery(order_id=order_id, driver_id=current_user.id)


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
    *   **Delivery**: the completed delivery record with all timing fields populated

    Raises:
    *   **HTTPException** (status_code = 400): if delivery has not been started yet, or has already been completed
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user is not the assigned driver for this delivery
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    from app.repositories.order_repo import load_orders, save_orders
    from app.services.order_service import send_status_notification

    delivery = await complete_delivery(order_id=order_id, driver_id=current_user.id)

    orders = load_orders()
    for order in orders:
        if order.get("id") == order_id:
            order["status"] = "delivered"
            save_orders(orders)
            await send_status_notification(order)
            break

    return delivery


@router.get("/{order_id}", response_model=Delivery, status_code=200)
def get_delivery_route(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    **Retrieves the delivery record for a given order. Accessible by any authenticated user.**

    Parameters:
    *   **order_id** (int): the identifier of the order
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **Delivery**: the delivery record for this order

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 404): if no delivery record is found for this order
    """
    return get_delivery_by_order(order_id=order_id)