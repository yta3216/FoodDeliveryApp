"""
This module defines the basic order schema for the application.
An order is created when a Customer confirms their order, transitioning
from a cart to an order.
Any updates to the order details should follow this schema.
"""
from typing import Literal
from pydantic import BaseModel


class Order(BaseModel):
    """
    **Defines the attributes of an order.**

    Attributes:
    *   **id** (int): the identifier of the order object
    *   **customer_id** (str): the identifier of the customer who placed the order
    *   **restaurant_id** (int): the identifier of the restaurant who will fulfill this order
    *   **delivery_id** (int): the identifier of the delivery driver who will deliver the order
    *   **receipt_id** (int): the identifier of the receipt this order was created from. use receipt to access items and pricing
    *   **status** (str): the order's status (pending, preparing, delivering, delivered, etc.)
    *   **distance_km** (float): distance from customer to restaurant in km, used for driver assignment and eta calculation
    *   **date_created** (str): the date the order was created
    """
    id: int
    customer_id: str
    restaurant_id: int = 0
    delivery_id: int = 0
    receipt_id: int = 0
    status: str = "pending"
    distance_km: float = 0.0
    date_created: str | None = None


class OrderAcceptReject(BaseModel):
    """
    **Defines the attributes required for a manager to accept or reject a pending order.**

    Attributes:
    *   **status** (str): the new status. must be either *accepted* or *rejected*
    """
    status: Literal["accepted", "rejected"]