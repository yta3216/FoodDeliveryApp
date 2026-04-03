"""
This module implements logic for payment processing.
Only when payment passes validation is the order created.
"""

import datetime

from fastapi import HTTPException

from app.schemas.user_schema import Customer
from app.schemas.payment_schema import PaymentRequest, OrderPaymentResponse
from app.schemas.receipt_schema import Receipt
from app.services.order_service import create_order_from_receipt
from app.services.notification_service import Notification
from app.services.receipt_service import get_receipt, refresh_receipt
from app.services.restaurant_service import get_restaurant_by_id
from app.services.config_service import get_tax_rate

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

async def _check_duplicate(receipt_id: int, current_user: Customer) ->  None:
    """
    Checks if a payment for this receipt id is already being processed.
    Notifies customer if there is a duplicate payment.

    Parameters:
        receipt_id (int): the receipt_id to check
        current_user (Customer): the authenticated customer

    Raises:
        HTTPException (status_code = 400): if receipt_id is already being processed
    """

    if receipt_id in _processing:
        notification = Notification(
            message = f"Duplicate payment detected for receipt #{receipt_id}. Your payment is already being processed.", 
            user_ids = [current_user.id])
        await notification.send_to_users()
        raise HTTPException(status_code=400, detail="Duplicate payment submission. Please wait.")

async def _check_fees(receipt: Receipt, current_user: Customer) -> None:
    """
    Checks if the restaurant's delivery fee or tax rate has changed since the receipt was created.
    Updates the receipt and raises 409 if it has changed.

    Parameters:
        receipt (Receipt): the receipt to check
        current_user (Customer): the authenticated customer

    Raises:
        HTTPException (status_code = 409): if the delivery fee or tax rate has changed
    """
    
    restaurant = get_restaurant_by_id(receipt.restaurant_id)
    if restaurant.delivery_fee != receipt.delivery_fee:
        refresh_receipt(receipt.id, current_user)
        raise HTTPException(status_code=409, detail="The restaurant's delivery fee has changed. Please try again.")
    
    if round(get_tax_rate() * receipt.subtotal, 2) != receipt.tax:
        refresh_receipt(receipt.id, current_user)
        raise HTTPException(status_code=409, detail="The tax rate has changed. Please try again.")

async def _execute_payment(payment: PaymentRequest, current_user: Customer, receipt: Receipt) -> OrderPaymentResponse:
    """
    Validates card details and create order if payment is successful
    Notifies the customer if payment failed

    Parameters:
        payment (PaymentRequest): the payment details
        current_user (Customer): the authenticated customer
        receipt (Receipt): the receipt to create the order from
    
    Returns:
        OrderPaymentResponse: contains payment_status, message, and the create order if successful
    
    Raises:
        HTTPException (status_code = 400): if payment validation fails
    """
    is_valid, error_message = _validate_payment(payment)

    if not is_valid:
        notification = Notification(
            message=f"Payment failed: {error_message} Please try again.",
            user_ids=[current_user.id]
        )
        await notification.send_to_users()
        raise HTTPException(status_code=400, detail=error_message)
 
    order = await create_order_from_receipt(current_user, receipt)
 
    return OrderPaymentResponse(
        payment_status="success",
        message="Payment successful. Your order has been placed.",
        order=order
    )
    
async def process_payment(payment: PaymentRequest, current_user: Customer) -> OrderPaymentResponse:
    """
    Full payment flow breakdown:
    1. Checks for duplicated payment
    2. Loads and validates the receipt
    3. Checks updates on delivery fee and taxes, refresh receipt
    4. Validate card details and create order if payment is successful

    Parameters:
        payment (PaymentRequest): the payment details submitted by the customer
        current_user (Customer): the authenticated user with role customer

    Returns:
        OrderPaymentResponse: contains payment_status, message, and the created order on success

    Raises:
        HTTPException (status_code = 400): if duplicate payments or failed payment validation
        HTTPException (status_code = 409): if either the delivery fee or tax rate has changed since the receipt was created. Will auto-refresh the receipt.
    """
    await _check_duplicate(payment.receipt_id, current_user)
 
    _processing.add(payment.receipt_id)
 
    try:
        receipt = get_receipt(payment.receipt_id)
        await _check_fees(receipt, current_user)
        return await _execute_payment(payment, current_user, receipt)
 
    finally:
        _processing.discard(payment.receipt_id)
    