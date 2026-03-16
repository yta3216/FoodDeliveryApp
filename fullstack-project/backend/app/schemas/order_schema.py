"""
This module defines the basic order schema for the application.
An order is created when a Customer confirms their order, transitioning
from a cart to an order.
Any updates to the order details should follow this schema.
"""
from typing import Literal
from pydantic import BaseModel, Field


class OrderItem(BaseModel):
    menu_item_id: int
    qty: int


class Order(BaseModel):
    """
    **Defines the attributes of an order.**
    Attributes:
    *   **id** (int): the identifier of the order object
    *   **customer_id** (str): the identifier of the customer who placed the order
    *   **restaurant_id** (int): the identifier of the restaurant who will fulfill this order
    *   **delivery_id** (int): the identifier of the delivery driver who will deliver the order
    *   **receipt_id** (int): the identifier of the receipt this order was created from
    *   **status** (str): the order's status (pending, preparing, delivered, etc.)
    *   **distance_km** (float): distance from customer to restaurant in km
    *   **delivery_fee** (float): the fee associated with delivering the order
    *   **tax** (float): taxes for the order
    *   **subtotal** (float): price of items before fees and tax
    *   **date_created** (str): the date the order was created
    """
    id: int
    customer_id: str
    restaurant_id: int = 0
    delivery_id: int = 0
    receipt_id: int = 0
    items: list[OrderItem] = Field(default_factory=list)
    status: str = "pending"
    distance_km: float = 0.0
    delivery_fee: float = 0.0
    tax: float = 0.0
    subtotal: float = 0.0
    date_created: str = None


class OrderStatusUpdate(BaseModel):
    """
    **Defines the attributes of an update to the order status.**
    Attributes:
    *   **status** (str): the updated status. must be either "accepted" or "rejected"
    """
    status: Literal["accepted", "rejected"]


# schema for customer to update items on a pending order
class OrderItemsUpdate(BaseModel):
    items: list[OrderItem] = Field(default_factory=list)


# schema for customer to create an order, includes distance from restaurant
class OrderCreate(BaseModel):
    distance_km: float = 0.0