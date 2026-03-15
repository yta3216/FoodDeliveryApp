"""
This module defines the schema for payment processing.
Payment is simulated - no real payment gateway is used.
Any updates to payment details should follow this schema.

"""

from pydantic import BaseModel
from app.schemas.order_schema import Order

class PaymentRequest(BaseModel):
    """
    **Defines the attributes required to submit a payment.**
    Attributes:
    *   **card_number** (str): the card number. must be exactly 16 digits
    *   **expiry_month** (int): the card's expiry month. must be between 1 and 12
    *   **expiry_year** (int): the card's expiry year
    *   **cvv** (str): the card's CVV. must be 3 or 4 digits
    *   **cardholder_name** (str): the name of the cardholder. must not be empty
    """
    card_number: str
    expiry_month: int
    expiry_year: int
    cvv: str
    cardholder_name: str

class PaymentResponse(BaseModel):
    """
    **Defines the attributes returned after a payment attempt.**
    Attributes:
    *   **payment_status** (str): the result of the payment attempt. either "success" or "failed"
    *   **message** (str): a human-readable message describing the result
    *   **order** (Order | None): the created order if payment was successful, otherwise None
    """
    payment_status: str
    message: str
    order: Order | None = None