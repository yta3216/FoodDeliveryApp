"""
This module defines the basic cart schema for the application.
An empty cart is created when a Customer is created, but the cart
must be initiated with a Menu ID when the customer begins adding items.

A cart can be deleted by simply overriding the existing cart with a new
Cart() object, restoring values to their defaults.

Any updates to the cart details should follow this schema.
"""

from typing import List
from pydantic import BaseModel, Field

# generic cart item schema. we store the MenuItem ID rather than the item itself in the cart to save storage.
class CartItem(BaseModel):
    menu_item_id: int
    qty: int

# schema to add an item to cart
class CartItem_Create(BaseModel):
    menu_item_id: int
    qty: int

# schema to update cart item qty. id contained in url
class CartItem_Update(BaseModel):
    new_qty: int

# generic cart schema
class Cart(BaseModel):
    restaurant_id: int = 0
    cart_items: List[CartItem] = Field(default_factory=list)
