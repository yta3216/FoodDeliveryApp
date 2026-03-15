"""
This module defines the API routes for payment processing.
The checkout endpoint is the single entry point for submitting payment.
An order is only created only when payment succeeds.
"""

from fastapi import APIRouter, Depends

from app.schemas.payment_schema import PaymentRequest, PaymentResponse
from app.schemas.user_schema import Customer
from app.services.user_service import get_customer
from app.services.payment_service import process_payment

router = APIRouter(prefix="/payment", tags=["payment"])


@router.post("/checkout", response_model=PaymentResponse, status_code=201)
async def checkout_route(
    payment: PaymentRequest,
    current_user: Customer = Depends(get_customer)
):
    """
    **Submits payment for the customer's current cart. Creates an order only if payment succeeds.**

    Parameters:
    *   **payment** (PaymentRequest): the card details submitted by the customer
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument

    Returns:
    *   **PaymentResponse**: contains payment_status, message, and the created order on success
    
    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 400): if payment validation fails or cart is empty. no order is created
    """
    return await process_payment(payment, current_user)