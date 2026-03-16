"""
This module defines the API routes for order management.
"""
from fastapi import APIRouter, Depends
from app.schemas.order_schema import (
    Order,
    OrderAcceptReject
)
from app.schemas.user_schema import Customer, User
from app.services.user_service import get_customer
from app.services.order_service import (
    get_orders_for_customer,
    get_orders_for_restaurant,
    cancel_order,
    accept_reject_order
)
from app.services.restaurant_service import check_manager
from app.auth import require_role
from app.schemas.user_schema import UserRole

router = APIRouter(prefix="/order", tags=["order"])

@router.get("/customer", response_model=list[Order], status_code=200, dependencies=[Depends(get_customer)])
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

@router.get("/restaurant/{restaurant_id}", response_model=list[Order], status_code=200, dependencies=[Depends(check_manager)])
def get_orders_for_restaurant_route(restaurant_id: int, current_user: User = Depends(check_manager)):
    """
    **Retrieves all orders associated with a given restaurant, which must be called by one of the restaurant's managers.**

    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant whose orders have been requested
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **list[Order]**: all orders associated with this restaurant sorted by date_created

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not "manager" or user is not a manager of the provided restaurant
    *   **HTTPException** (status_code = 404): restaurant_id not found in restaurants.json
    """
    return get_orders_for_restaurant(restaurant_id=restaurant_id, manager_id=current_user.id)

@router.delete("/{order_id}", response_model=Order, status_code=200, dependencies=[Depends(get_customer)])
async def cancel_order_route(order_id: int, current_user: Customer = Depends(get_customer)):
    """
    **Cancels an order associated with the logged-in customer. Must have status:** *pending.*

    Parameters:
    *   **order_id** (int): the identifier of the order to be cancelled
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **Order**: the cancelled order

    Raises:
    *   **HTTPException** (status_code = 401): if current user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if current user's role is not *customer*
    *   **HTTPException** (status_code = 409): if current user's id does not match the order's customer id
    *   **HTTPException** (status_code = 400): if order has a status other than "pending"
    *   **HTTPException** (status_code = 404): if order is not found in orders.json
    """
    return await cancel_order(order_id=order_id, current_user=current_user)

@router.patch("/{order_id}/status", response_model=Order, status_code=200)
async def accept_reject_order_route(order_id: int, body: OrderAcceptReject, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    """
    **This method is used by restaurant managers to accept or reject pending orders for their restaurant.**

    Parameters:
    *   **order_id** (int): the identifier of the order with the requested status change
    *   **body** (OrderAcceptReject): the new order status
    *   **current_user** (User): the authenticated user with role *manager*. automatically passed as argument.

    Returns:
    *   **Order**: the order with updated status

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *manager*, or if provided user_id is not in restaurant's list of managers
    *   **HTTPException** (status_code = 400): if order has a status other than "pending"
    *   **HTTPException** (status_code = 404): if order is not found in orders.json, or order's restaurant id not found in restaurants.json
    """
    return await accept_reject_order(order_id=order_id, new_status=body.status, manager_id=current_user.id)
