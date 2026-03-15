"""
This module defines the basic order schema for the application.
An order is created when a Customer confirms their order, transitioning 
from a cart to an order.

Any updates to the order details should follow this schema.
"""

from typing import Literal
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    """
    **Defines the attributes of a generic order item.**

    Attributes:
    *   **menu_item_id** (int): the identifier of this item on its associated menu
    *   **qty** (int): the amount of this item in the order
    """
    menu_item_id: int
    qty: int

class OrderItem_Create(BaseModel):
    """
    **Defines the attributes required for the creation of an order item.**

    Attributes:
    *   **menu_item_id** (int): the identifier of this item on its associated menu
    *   **qty** (int): the amount of this item in the order
    """
    menu_item_id: int
    qty: int

class OrderItem_Update(BaseModel):
    """
    **Defines the attributes required to update an item in the order. Item ID is passed by URL.**

    Attributes:
    *   **new_qty** (int): the new quantity of this item in the order
    """
    new_qty: int

class Order(BaseModel):
    """
    **Defines the attributes of an order.**

    Attributes:
    *   **id** (int): the identifier of the order object
    *   **customer_id** (str): the identifier of the customer who placed the order
    *   **restaurant_id** (int): the identifier of the restaurant who will fulfill this order
    *   **delivery_id** (int): the identifier of the delivery driver who will deliver the order
    *   **items** (list[OrderItem]): a list of the items included in the order
    *   **status** (str): the order's status (pending, preparing, delivered, etc.)
    *   **delivery_fee** (float): the fee associated with delivering the order
    *   **tax** (float): taxes for the order
    *   **subtotal** (str): price of items in order without considering additional fees such as tax and delivery fee
    *   **date_created** (str): the date the order was created
    """
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

class OrderStatusUpdate(BaseModel):
    """
    **Defines the attributes of an update to the order status.**

    Attributes:
    *   **status** (str): the updated status. must be either "accepted" or rejected"
    """
    status: Literal["accepted","rejected"]
