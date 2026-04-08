"""
This module defines the API routes for order management.
"""
from fastapi import APIRouter, Depends
from app.schemas.order_schema import Order, OrderAcceptReject
from app.schemas.user_schema import Customer, User
from app.services.user_service import get_customer
from app.services.order_service import (
    get_orders_for_customer,
    get_orders_for_restaurant,
    cancel_order,
    accept_reject_order,
    mark_order_ready,
)
from app.services.restaurant_service import check_manager
from app.auth import require_role
from app.schemas.user_schema import UserRole

router = APIRouter(prefix="/order", tags=["order"])


@router.get("/customer", response_model=list[Order], status_code=200)
def get_orders_for_customer_route(current_user: Customer = Depends(get_customer)):
    """
    **Retrieves all orders associated with the logged-in customer.**

    Parameters:
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **list[Order]**: all orders that this customer has placed

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    """
    return get_orders_for_customer(current_customer=current_user)


@router.get("/restaurant/{restaurant_id}", response_model=list[Order], status_code=200)
def get_orders_for_restaurant_route(restaurant_id: int, current_user: User = Depends(check_manager)):
    """
    **Retrieves all orders associated with a given restaurant. Must be called by one of the restaurant's managers.**

    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant whose orders have been requested
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **list[Order]**: all orders associated with this restaurant

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *manager* or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): if restaurant_id is not found
    """
    return get_orders_for_restaurant(restaurant_id=restaurant_id, manager_id=current_user.id)


@router.delete("/{order_id}", response_model=Order, status_code=200)
async def cancel_order_route(order_id: int, current_user: Customer = Depends(get_customer)):
    """
    **Cancels a pending order. Only the customer who placed the order may cancel it.**

    Parameters:
    *   **order_id** (int): the identifier of the order to be cancelled
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **Order**: the cancelled order

    Raises:
    *   **HTTPException** (status_code = 401): if current user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if current user did not place this order
    *   **HTTPException** (status_code = 400): if order status is not *pending*
    *   **HTTPException** (status_code = 404): if order is not found
    """
    return await cancel_order(order_id=order_id, current_user=current_user)


@router.patch("/{order_id}/status", response_model=Order, status_code=200)
async def accept_reject_order_route(order_id: int, body: OrderAcceptReject, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    """
    **Allows a restaurant manager to accept or reject a pending order for their restaurant.**
    **If accepted and within delivery radius, a driver is assigned. If no driver is available, order goes to** *waiting_for_driver.*
    **If the order is outside the restaurant's delivery radius, it is automatically rejected.**

    Parameters:
    *   **order_id** (int): the identifier of the order with the requested status change
    *   **body** (OrderAcceptReject): contains the new status, either *accepted* or *rejected*
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **Order**: the order with updated status

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *manager*, or user is not a manager of this order's restaurant
    *   **HTTPException** (status_code = 400): if order status is not *pending*
    *   **HTTPException** (status_code = 404): if order or restaurant is not found
    """
    return await accept_reject_order(order_id=order_id, new_status=body.status, manager_id=current_user.id)

@router.patch("/{order_id}/ready", response_model=Order, status_code=200)
async def mark_order_ready_route(order_id: int, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    """
    **Marks an order as ready for delivery. Must be called by a restaurant manager.**

    Parameters:
    *   **order_id** (int): the identifier of the order to be marked as ready
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **Order**: the order with updated status

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *manager*, or user is not a manager of this order's restaurant
    *   **HTTPException** (status_code = 400): if order status is not *pending*
    *   **HTTPException** (status_code = 404): if order or restaurant is not found
    """
    return await mark_order_ready(order_id=order_id, manager_id=current_user.id)