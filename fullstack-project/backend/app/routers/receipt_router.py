"""
This module defines the API routes for receipt management.
A receipt is generated from the customer's cart before payment is submitted.
"""

from fastapi import APIRouter, Depends

from app.schemas.receipt_schema import Receipt
from app.schemas.user_schema import Customer
from app.services.user_service import get_customer
from app.services.receipt_service import create_receipt, refresh_receipt

router = APIRouter(prefix="/receipt", tags=["receipt"])


@router.get("", response_model=Receipt, status_code=200)
def get_receipt_route(current_user: Customer = Depends(get_customer)):
    """
    **Generates and saves a priced receipt from the customer's current cart.
    The cart is not modified and no order is created.
    The returned receipt_id must be passed to POST /payment/checkout.**

    Parameters:
        **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
        **Receipt**: the saved receipt with full cost breakdown and a receipt_id

    Raises:
        **HTTPException** (status_code = 401): if user's token is invalid or expired
        **HTTPException** (status_code = 403): if user's role is not *customer*
        **HTTPException** (status_code = 400): if the cart is empty
        **HTTPException** (status_code = 404): if the cart's restaurant is not found
    """
    return create_receipt(current_user)

@router.post("/refresh/{receipt_id}", response_model=Receipt, status_code=200)
def refresh_receipt_route(receipt_id: int, current_user: Customer = Depends(get_customer)):
    """
    **Generates a new receipt snapshot for an existing receipt.
    This route is used for when details of the Receipt differ from the existing values in other services
    (ex. restaurant delivery fee has changed since the receipt was created)**

    Raises:
        **HTTPException** (status_code = 401): if user's token is invalid or expired
        **HTTPException** (status_code = 403): if the receipt belongs to another user
        **HTTPException** (status_code = 404): if the receipt is not found
        **HTTPException** (status_code = 409): if the cart restaurant has changed since the receipt was created
    """
    return refresh_receipt(receipt_id, current_user)
