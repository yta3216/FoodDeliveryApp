"""
This module defines the API routes for order management.
"""
from fastapi import APIRouter, Depends
from app.schemas.order_schema import (
    Order,
    OrderStatusUpdate
)
from app.schemas.user_schema import Customer,User
from app.services.user_service import (
    get_customer
)
from app.services.order_service import (
    create_order_from_cart,
    get_orders_for_customer,
    get_orders_for_restaurant,
    cancel_order,
    update_order_status,
)
from app.services.restaurant_service import check_manager
from app.auth import require_role
from app.schemas.user_schema import UserRole

router = APIRouter(prefix="/order", tags=["order"])

@router.post("", response_model=Order, status_code=201, dependencies=[Depends(get_customer)])
def create_order_from_cart_route(current_user: Customer = Depends(get_customer)):
    """
    **Converts a logged-in customer's cart to an order, meaning they have paid for the items.**

    Parameters: None

    Returns:
    *   **Order**: the newly created order
    """
    return create_order_from_cart(current_user)

@router.get("/customer", response_model=list[Order], status_code=200, dependencies=[Depends(get_customer)])
def get_orders_for_customer_route(current_user: Customer = Depends(get_customer)):
    """
    **Retrieves all orders associated with the logged-in customer.**
    
    Parameters: None

    Returns:
    *   **list[Order]**: all orders that this customer has placed
    """
    return get_orders_for_customer(current_customer=current_user)

@router.get("/restaurant/{restaurant_id}", response_model=list[Order], status_code=200, dependencies=[Depends(check_manager)])
def get_orders_for_restaurant_route(restaurant_id: int, current_user: User = Depends(check_manager)):
    """
    **Retrieves all orders associated with a given restaurant, which must be called by one of the restaurant's managers.**
    
    Parameters:
    *   **restaurant_id** (int): the identifier of the restaurant whose orders have been requested

    Returns:
    *   **list[Order]**: all orders associated with this restaurant
    """
    return get_orders_for_restaurant(restaurant_id=restaurant_id, manager_id=current_user.id)

@router.delete("/{order_id}", response_model=Order, status_code=200, dependencies=[Depends(get_customer)])
def cancel_order_route(order_id:int, current_user: Customer = Depends(get_customer)):
    """
    **Cancels an order associated with the logged-in customer. Must have status:** pending.*
    
    Parameters:
    *   **order_id** (int): the identifier of the order to be cancelled

    Returns:
    *   **Order**: the cancelled order
    """
    return cancel_order(order_id=order_id, current_user=current_user)

@router.patch("/{order_id}/status", response_model=Order, status_code=200)
def update_order_status_route(order_id:int, body: OrderStatusUpdate, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    """
    **This method is used by restaurant managers to accept or reject pending orders for their restaurant.**
    
    Parameters:
    *   **order_id** (int): the identifier of the order with the requested status change
    *   **body** (OrderStatusUpdate): the new order status

    Returns:
    *   **Order**: the order with updated status
    """
    return update_order_status(order_id=order_id, new_status=body.status, manager_id=current_user.id)

