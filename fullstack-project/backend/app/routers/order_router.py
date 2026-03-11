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


router = APIRouter(prefix="/order", tags=["order"])

@router.post("", response_model=Order, status_code=201, dependencies=[Depends(get_customer)])
def create_order_from_cart_route(current_user: Customer = Depends(get_customer)):
    return create_order_from_cart(current_user)

@router.get("/customer", response_model=list[Order], status_code=200, dependencies=[Depends(get_customer)])
def get_orders_for_customer_route(current_user: Customer = Depends(get_customer)):
    return get_orders_for_customer(current_customer=current_user)

@router.get("/restaurant/{restaurant_id}", response_model=list[Order], status_code=200, dependencies=[Depends(check_manager)])
def get_orders_for_restaurant_route(restaurant_id: int, current_user: User = Depends(check_manager)):
    return get_orders_for_restaurant(restaurant_id=restaurant_id, manager_id=current_user.id)

# Delete pending order for customer
@router.delete("/{order_id}", response_model=Order, status_code=200, dependencies=[Depends(get_customer)])
def cancel_order_route(order_id:int, current_user: Customer = Depends(get_customer)):
    return cancel_order(order_id=order_id, current_user=current_user)

# Accept/reject pending order for manager
@router.patch("/{order_id}/status", response_model=Order, status_code=200, dependencies=[Depends(check_manager)])
def update_order_status_route(order_id:int, body: OrderStatusUpdate, current_user: User = Depends(check_manager)):
    return update_order_status(order_id=order_id, new_status=body.status, manager_id=current_user.id)

