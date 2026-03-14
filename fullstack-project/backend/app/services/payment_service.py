"""
This module implements logic for payment processing.
Only when payment passes validation is the order created.
"""

import datetime

from fastapi import HTTPException

from app.schemas.user_schema import Customer
from app.schemas.payment_schema import PaymentRequest, PaymentResponse
from app.services.order_service import create_order_from_cart
from app.services.notification_service import Notification


def _validate_payment(payment: PaymentRequest) -> tuple[bool, str]:

    # Cardholder name must not be empty
    if not payment.cardholder_name.strip():
        return False, "Cardholder name cannot be empty."

    # Card number must be exactly 16 digits
    if not payment.card_number.isdigit() or len(payment.card_number) != 16:
        return False, "Invalid card number. Must be exactly 16 digits."

    # Hardcoded declined card for testing
    if payment.card_number == "0000000000000000":
        return False, "Card was declined."

    # CVV must be 3 or 4 digits
    if not payment.cvv.isdigit() or len(payment.cvv) not in (3, 4):
        return False, "Invalid CVV. Must be 3 or 4 digits."

    # Expiry month must be valid
    if payment.expiry_month < 1 or payment.expiry_month > 12:
        return False, "Invalid expiry month."

    # Expiry must not be in the past
    now = datetime.datetime.now(datetime.timezone.utc)
    if (payment.expiry_year, payment.expiry_month) < (now.year, now.month):
        return False, "Card has expired."

    return True, ""


async def process_payment(payment: PaymentRequest, current_user: Customer) -> PaymentResponse:
 
    is_valid, error_message = _validate_payment(payment)
 
    if not is_valid:
        notification = Notification(
            message=f"Payment failed: {error_message} Please try again.",
            user_ids=[current_user.id]
        )
        await notification.send_to_users()
        raise HTTPException(status_code=400, detail=error_message)
 
    # Payment passed
    order = await create_order_from_cart(current_user)
 
    return PaymentResponse(
        payment_status="success",
        message="Payment successful. Your order has been placed.",
        order=order
    )