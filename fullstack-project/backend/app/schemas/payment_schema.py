"""
This module defines the schema for payment processing.
Payment is simulated - no real payment processes

"""

from pydantic import BaseModel
from app.schemas.order_schema import Order

class PaymentRequest(BaseModel):
    card_number: str
    expiry_month: int
    expiry_year: int
    cvv: str
    cardholder: str

class PaymentResponse(BaseModel):
    payment_status: str
    message: str
    order: Order | None = None