"""
This module defines the basic cart schema for the application.
An empty cart is created when a Customer is created, but the cart
must be initiated with a Menu ID when the customer begins adding items.

A cart can be deleted by simply overriding the existing cart with a new
Cart() object, restoring values to their defaults.

Any updates to the cart details should follow this schema.
"""

from pydantic import BaseModel, Field

class CartItem(BaseModel):
    """
    **Defines the attributes of a generic cart item.**

    Attributes:
    *   **menu_item_id** (int): the identifier of this item on its associated menu
    *   **qty** (int): the amount of this item in the cart
    """
    menu_item_id: int
    qty: int

class CartItem_Create(BaseModel):
    """
    **Defines the attributes required for cart item creation.**

    Attributes:
    *   **menu_item_id** (int): the identifier of this item on its associated menu
    *   **qty** (int): the amount of this item in the cart
    """
    menu_item_id: int
    qty: int

class CartItem_Update(BaseModel):
    """
    **Defines the attributes required to update an item in the cart. Item ID is passed by URL.**

    Attributes:
    *   **new_qty** (int): the new quantity of this item in the cart
    """
    new_qty: int

class Cart(BaseModel):
    """
    **Defines the attributes required to create a cart.**

    Attributes:
    *   **restaurant_id** (int): the identifier of the restaurant which this cart orders from.
    *   **cart_items** (list[CartItem]): intitial items to be added to the cart *(optional)*.
    *   **promo_code** (str | None): the promo code applied to this cart, if any *(optional)*.
    """
    restaurant_id: int = 0
    cart_items: list[CartItem] = Field(default_factory=list)
    promo_code: str | None = None
