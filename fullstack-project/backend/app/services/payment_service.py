"""
This module implements logic for payment processing.
Only when payment passes validation is the order created.
"""

import datetime

from fastapi import HTTPException

from app.schemas.user_schema import Customer
from app.schemas.payment_schema import PaymentRequest, PaymentResponse
from app.services.order_service import create_order_from_receipt
from app.services.notification_service import Notification
from app.services.receipt_service import get_receipt, refresh_receipt
from app.services.restaurant_service import get_restaurant_by_id

_processing: set[int] = set()

def _validate_payment(payment: PaymentRequest) -> tuple[bool, str]:
    """
    Validates simulated payment details.

    Parameters:
        payment (PaymentRequest): the payment details to validate

    Returns:
        tuple[bool, str]: a tuple of (is_valid, error_message). error_message is empty on success
    """

    if not payment.cardholder_name.strip():
        return False, "Cardholder name cannot be empty."

    if not payment.card_number.isdigit() or len(payment.card_number) != 16:
        return False, "Invalid card number. Must be exactly 16 digits."

    if payment.card_number == "0000000000000000":
        return False, "Card was declined."

    if not payment.cvv.isdigit() or len(payment.cvv) not in (3, 4):
        return False, "Invalid CVV. Must be 3 or 4 digits."

    if payment.expiry_month < 1 or payment.expiry_month > 12:
        return False, "Invalid expiry month."

    now = datetime.datetime.now(datetime.timezone.utc)
    if (payment.expiry_year, payment.expiry_month) < (now.year, now.month):
        return False, "Card has expired."

    return True, ""

async def process_payment(payment: PaymentRequest, current_user: Customer) -> PaymentResponse:
    """
    Validates payment and, only on success, creates the order.
    Blocks duplicated submission for the same receipt_id that occur in quick succession.

    Parameters:
        payment (PaymentRequest): the payment details submitted by the customer
        current_user (Customer): the authenticated user with role customer

    Returns:
        PaymentResponse: contains payment_status, message, and the created order on success

    Raises:
        HTTPException (status_code = 400): if payment validation fails or duplicate submission detected
        HTTPException (status_code = 409): if the restaurant's delivery fee has changed since the receipt was created.
    """
    
    if payment.receipt_id in _processing:
        notification = Notification(
        message=f"Duplicate payment detected for receipt #{payment.receipt_id}. Your payment is already being processed.",
        user_ids=[current_user.id]
        )
        await notification.send_to_users()
        raise HTTPException(status_code=400, detail="Duplicate payment submission.Please wait...")
    
    _processing.add(payment.receipt_id)

    try:
        receipt = get_receipt(payment.receipt_id)

        if (get_restaurant_by_id(receipt.restaurant_id)["delivery_fee"] != receipt.delivery_fee):
            refresh_receipt(receipt.id, current_user)
            raise HTTPException(status_code=409, detail="The restaurant's delivery fee has changed. Please try again.")

        is_valid, error_message = _validate_payment(payment)
    
        if not is_valid:
            notification = Notification(
                message=f"Payment failed: {error_message} Please try again.",
                user_ids=[current_user.id]
            )
            await notification.send_to_users()
            raise HTTPException(status_code=400, detail=error_message)
    
        order = await create_order_from_receipt(current_user, receipt)
    
        return PaymentResponse(
            payment_status="success",
            message="Payment successful. Your order has been placed.",
            order=order
        )
    
    finally:
        _processing.discard(payment.receipt_id)