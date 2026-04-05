"""
This module defines the schema for promotional codes.
Promo codes can apply different types of discounts to a customer's order.
"""

from enum import Enum
from pydantic import BaseModel


class PromoType(str, Enum):
    """
    **Enumeration of supported promo code discount types.**

    Attributes:
    *   **FIXED_AMOUNT**: deducts a fixed dollar amount from the order total
    *   **FREE_DELIVERY**: sets the delivery fee to zero
    *   **PERCENTAGE**: deducts a percentage of the subtotal
    """
    FIXED_AMOUNT = "fixed_amount"
    FREE_DELIVERY = "free_delivery"
    PERCENTAGE = "percentage"


class PromoCode(BaseModel):
    """
    **Defines the attributes of a promotional code.**

    Attributes:
    *   **id** (int): the identifier of the promo code
    *   **code** (str): the alphanumeric code customers enter at checkout
    *   **description** (str): a description of the discount
    *   **type** (PromoType): the type of discount
    *   **value** (float): the discount value. for fixed_amount: dollar amount. for percentage: percent (0-100). unused for free_delivery
    *   **min_order_value** (float): minimum subtotal required to apply this code
    *   **expiry_date** (str | None): optional expiry date in YYYY-MM-DD format
    *   **is_active** (bool): whether the code can currently be used
    *   **is_public** (bool): whether the code is visible to customers on the promotions listing
    *   **is_first_order_only** (bool): whether the code can only be used on a customer's first order
    *   **usage_count** (int): total number of times this code has been used
    *   **used_by_customer_ids** (list[str]): list of customer ids who have already used this code
    """
    id: int
    code: str
    description: str = ""
    type: PromoType
    value: float = 0.0
    min_order_value: float = 0.0
    expiry_date: str | None = None
    is_active: bool = True
    is_public: bool = True
    is_first_order_only: bool = False
    usage_count: int = 0
    used_by_customer_ids: list[str] = []


class PromoApplyRequest(BaseModel):
    """
    **Defines the attributes required for a customer to apply a promo code to their cart.**

    Attributes:
    *   **code** (str): the promo code to apply
    """
    code: str


class PromoPublic(BaseModel):
    """
    **Defines the publicly visible attributes of a promo code shown to customers.**

    Attributes:
    *   **code** (str): the promo code string
    *   **description** (str): a description of the discount
    *   **type** (PromoType): the type of discount
    *   **value** (float): the discount value
    *   **min_order_value** (float): minimum subtotal to use this code
    *   **expiry_date** (str | None): optional expiry date
    *   **is_first_order_only** (bool): whether this is restricted to first orders
    """
    code: str
    description: str
    type: PromoType
    value: float
    min_order_value: float
    expiry_date: str | None
    is_first_order_only: bool

class PromoCode_Create(BaseModel):
    """
    **Defines the attributes required for an admin to create a new promotional code.**
    id and usage tracking fields are assigned automatically.
 
    Attributes:
    *   **code** (str): the alphanumeric code customers will enter at checkout
    *   **description** (str): a description of the discount
    *   **type** (PromoType): the type of discount this code applies
    *   **value** (float): the discount value. for fixed_amount: dollar amount. for percentage: percent (0-100). unused for free_delivery
    *   **min_order_value** (float): minimum subtotal required to apply this code *(default 0.0)*
    *   **expiry_date** (str | None): optional expiry date in YYYY-MM-DD format
    *   **is_public** (bool): whether the code is visible to customers on the promotions listing *(default True)*
    *   **is_first_order_only** (bool): whether the code can only be used on a customer's first order *(default False)*
    """
    code: str
    description: str = ""
    type: PromoType
    value: float = 0.0
    min_order_value: float = 0.0
    expiry_date: str | None = None
    is_public: bool = True
    is_first_order_only: bool = False
 
 
class PromoCode_StatusUpdate(BaseModel):
    """
    **Defines the attributes required for an admin to activate or deactivate a promo code.**
 
    Attributes:
    *   **is_active** (bool): the new active status of the promo code
    """
    is_active: bool

