"""
This module defines the API routes for payment processing.
"""

from fastapi import APIRouter, Depends

from app.schemas.payment_schema import WalletTopUpRequest, PaymentResponse, OrderPaymentResponse
from app.schemas.user_schema import Customer
from app.schemas.receipt_schema import Receipt
from app.services.user_service import get_customer
from app.services.payment_service import checkout, topup_wallet

router = APIRouter(prefix="/payment", tags=["payment"])

@router.post("/topup-wallet", response_model=PaymentResponse, status_code=201)
async def topup_wallet_route(payment: WalletTopUpRequest, current_user: Customer = Depends(get_customer)):
    """
    **Submits payment to top up user's wallet.**

    Parameters:
    *   **payment** (WalletTopUpRequest): the payment details submitted by the customer
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument

    Returns:
    *   **PaymentResponse**: contains payment_status and message
    
    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 400): if payment validation fails
    """
    return topup_wallet(payment, current_user)

@router.post("/checkout", response_model=OrderPaymentResponse, status_code=201)
async def checkout_route(
    receipt: Receipt,
    current_user: Customer = Depends(get_customer)
):
    """
    **Submits payment for the customer's current cart. Creates an order only if payment succeeds.**

    Parameters:
    *   **payment** (PaymentRequest): the card details submitted by the customer
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument

    Returns:
    *   **OrderPaymentResponse**: contains payment_status, message, and the created order on success
    
    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 400): if payment validation fails or cart is empty. no order is created
    *   **HTTPException** (status_code = 409): if either the delivery fee or tax rate has changed since the receipt was created. Will auto-refresh the receipt.
    """
    return await checkout(receipt, current_user)