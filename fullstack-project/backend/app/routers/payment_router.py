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
):return await process_payment(payment, current_user)