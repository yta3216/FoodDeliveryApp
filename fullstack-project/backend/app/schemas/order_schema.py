"""
This module defines the basic order schema for the application.
An order is created when a Customer confirms their order, transiting from
a cart to an order.

An order can be deleted by simply overriding the existing order with a new
Order() object, restoring values to their defaults.

Any updates to the order details should follow this schema.
"""

from typing import List
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
    delivery_id: int = None | None # delivery_id is None until a delivery person is assigned to the order
    items: List[OrderItem] = Field(default_factory=list)
    status: str = "pending"
    delivery_fee: float = 0.0
    tax: float = 0.0
    total_price: float = 0.0