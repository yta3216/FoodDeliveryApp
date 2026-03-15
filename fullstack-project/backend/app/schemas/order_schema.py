"""
This module defines the basic order schema for the application.
An order is created when a Customer confirms their order, transiting from
a cart to an order.

Any updates to the order details should follow this schema.
"""

from typing import Literal
from pydantic import BaseModel, Field

# generic order item schema.
class OrderItem(BaseModel):
    menu_item_id: int
    qty: int

# schema to add an item to order
class OrderItem_Create(BaseModel):
    menu_item_id: int
    qty: int

# schema to update order item qty. id contained in url
class OrderItem_Update(BaseModel):
    new_qty: int

# generic order schema
class Order(BaseModel):
    id: int
    customer_id: str
    restaurant_id: int = 0
    delivery_id: int = 0
    items: list[OrderItem] = Field(default_factory=list)
    status: str = "pending"
    delivery_fee: float = 0.0
    tax: float = 0.0
    subtotal: float = 0.0
    date_created: str = None

# schema for manager to accept/reject pending order
class OrderStatusUpdate(BaseModel):
    status: Literal["accepted","rejected"]

