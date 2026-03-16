"""
This module defines the schema for order receipts.
A receipt is created when a customer requests a cost breakdown of their cart
before submitting payment. It is saved independently and referenced by the
order once payment is successful.

Any updates to receipt details should follow this schema.
"""

from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    """
    **Defines a single priced line item in a receipt.**

    Attributes:
    *   **menu_item_id** (int): the identifier of this item on its associated menu
    *   **name** (str): the name of the menu item at time of receipt creation
    *   **unit_price** (float): the price per unit of this item at time of receipt creation
    *   **qty** (int): the quantity of this item in the cart
    *   **line_total** (float): unit_price multiplied by qty
    """
    menu_item_id: int
    name: str
    unit_price: float
    qty: int
    line_total: float


class Receipt(BaseModel):
    """
    **Defines the attributes of a receipt. A receipt is a priced snapshot of a
    customer's cart created before payment is submitted. It is saved to storage
    and referenced by the order after a successful payment.**

    Attributes:
    *   **id** (int): the identifier of the receipt
    *   **customer_id** (str): the identifier of the customer who requested the receipt
    *   **restaurant_id** (int): the identifier of the restaurant being ordered from
    *   **items** (list[ReceiptItem]): priced line items from the cart at time of receipt creation
    *   **subtotal** (float): total price of items before tax and delivery fee
    *   **tax** (float): tax applied to the order
    *   **delivery_fee** (float): fee for delivering the order
    *   **total** (float): subtotal + tax + delivery_fee
    """
    id: int
    customer_id: str
    restaurant_id: int
    items: list[ReceiptItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    delivery_fee: float = 0.0
    distance_km: float = 0.0
    total: float = 0.0
    date_created: str = None
