"""
This module defines the API routes for order management.
"""
from fastapi import APIRouter, Depends
from app.schemas.order_schema import (
    Order
)
from app.schemas.user_schema import Customer
from app.services.user_service import (
    get_customer
)
from app.services.order_service import (
    create_order_from_cart,
    get_orders_for_customer
)

router = APIRouter(prefix="/order", tags=["order"])

@router.post("", response_model=Order, status_code=201, dependencies=[Depends(get_customer)])
def create_order_from_cart(current_user: Customer = Depends(get_customer)):
    return create_order_from_cart(current_user)

@router.get("/customer/{customer_id}", response_model=list[Order], status_code=200, dependencies=[Depends(get_customer)])
def get_orders_for_customer_route(current_user: Customer = Depends(get_customer)):
    return get_orders_for_customer(current_customer=current_user)