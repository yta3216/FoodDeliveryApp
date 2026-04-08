"""
This module defines the API routes for receipt management.
A receipt is generated from the customer's cart before payment is submitted.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.receipt_schema import Receipt
from app.schemas.user_schema import Customer
from app.services.user_service import get_customer
from app.services.receipt_service import create_receipt, get_receipt

router = APIRouter(prefix="/receipt", tags=["receipt"])


@router.get("", response_model=Receipt, status_code=200)
def get_receipt_route(distance_km: float = 0.0, current_user: Customer = Depends(get_customer)):
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
    return create_receipt(current_user, distance_km)

@router.get("/{receipt_id}", response_model=Receipt, status_code=200)
def get_receipt_by_id_route(receipt_id: int, current_user: Customer = Depends(get_customer)):
    """
    **Returns a generated receipt by its ID.**

    Parameters:
        **receipt_id** (int): the ID of the receipt to retrieve
        **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
        **Receipt**: the receipt with full cost breakdown and a receipt_id

    Raises:
        **HTTPException** (status_code = 401): if user's token is invalid or expired
        **HTTPException** (status_code = 403): if user's role is not *customer* or does not belong to the user
        **HTTPException** (status_code = 404): if the receipt is not found
    """
    receipt = get_receipt(receipt_id)
    if receipt.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this receipt")
    return receipt