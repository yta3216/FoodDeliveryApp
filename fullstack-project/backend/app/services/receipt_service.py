"""
This module implements business logic for receipt management.
A receipt is a priced snapshot of a customer's cart created before payment.
Cost calculations are handled here.

Any updates to receipt logic should follow this module.
"""

import datetime

from fastapi import HTTPException

from app.schemas.user_schema import Customer
from app.schemas.receipt_schema import Receipt, ReceiptItem
from app.repositories.receipt_repo import load_receipts, save_receipts
from app.services.cart_service import get_cart
from app.services.restaurant_service import get_restaurant_by_id


def create_receipt(current_user: Customer, distance_km: float = 0.0) -> Receipt:
    """
    **Calculates the cost of the customer's current cart and saves a receipt to storage.
    The cart is not modified. A new receipt is created each time this is called.**

    Parameters:
    *   **current_user** (Customer): the authenticated user with role *customer*
    *   **distance_km** (float): the distance in kilometers for delivery fee calculation

    Returns:
    *   **Receipt**: the saved receipt with full cost breakdown

    Raises:
    *   **HTTPException** (status_code = 400): if the cart is empty
    *   **HTTPException** (status_code = 404): if the cart's restaurant is not found
    """
    cart = get_cart(current_user)
    if cart.restaurant_id == 0:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    restaurant = get_restaurant_by_id(cart.restaurant_id)
    menu_items = {item["id"]: item for item in restaurant["menu"]["items"]}

    receipt_items = []
    subtotal = 0.0

    for cart_item in cart.cart_items:
        menu_item = menu_items.get(cart_item.menu_item_id)
        if menu_item:
            unit_price = menu_item.get("price", 0.0)
            line_total = round(unit_price * cart_item.qty, 2)
            subtotal += line_total
            receipt_items.append(ReceiptItem(
                menu_item_id=cart_item.menu_item_id,
                name=menu_item.get("name", ""),
                unit_price=unit_price,
                qty=cart_item.qty,
                line_total=line_total
            ))

    subtotal = round(subtotal, 2)
    tax = 0.0
    delivery_fee = 0.0
    total = round(subtotal + tax + delivery_fee, 2)

    receipts = load_receipts()
    new_id = max((r.get("id", 0) for r in receipts), default=0) + 1

    new_receipt = Receipt(
        id=new_id,
        customer_id=current_user.id,
        restaurant_id=cart.restaurant_id,
        items=receipt_items,
        subtotal=subtotal,
        tax=tax,
        delivery_fee=delivery_fee,
        distance_km=distance_km,
        total=total,
        date_created=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    receipts.append(new_receipt.model_dump())
    save_receipts(receipts)

    return new_receipt


def get_receipt(receipt_id: int) -> Receipt:
    """
    **Retrieves a saved receipt by its identifier.**

    Parameters:
    *   **receipt_id** (int): the identifier of the receipt to retrieve

    Returns:
    *   **Receipt**: the matching receipt

    Raises:
    *   **HTTPException** (status_code = 404): if receipt is not found
    """
    receipts = load_receipts()
    for receipt in receipts:
        if receipt.get("id") == receipt_id:
            return Receipt(**receipt)
    raise HTTPException(status_code=404, detail=f"Receipt '{receipt_id}' not found.")