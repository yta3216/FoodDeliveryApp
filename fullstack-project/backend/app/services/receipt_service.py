"""
This module implements business logic for receipt management.
A receipt is a priced snapshot of a customer's cart created before payment.
Cost calculations are handled here.

Any updates to receipt logic should follow this module.
"""

from fastapi import HTTPException

from app.schemas.user_schema import Customer
from app.schemas.receipt_schema import Receipt, ReceiptItem
from app.schemas.restaurant_schema import Combo, ComboType, MenuItem
from app.repositories.receipt_repo import load_receipts, save_receipts
from app.services.cart_service import get_cart
from app.services.restaurant_service import get_restaurant_by_id
from app.services.config_service import get_tax_rate
from app.services.promo_service import validate_promo, calculate_discount


def _calculate_combo_discount(cart_item_qty: dict[int, int], combos: list[Combo], menu_items: dict[int, MenuItem]) -> float:
    """
    Calculates the highest single applicable combo discount for the current cart.
    Only one combo can be applied per receipt.
    """
    if not combos:
        return 0.0

    best_discount = 0.0
    for combo in combos:
        if combo.type == ComboType.PERCENTAGE:
            combo_price = sum(menu_items[item_id].price * qty for item_id, qty in cart_item_qty.items() if item_id in combo.item_ids)
            discount_amount = combo_price * (combo.discount / 100)
            best_discount = max(best_discount, discount_amount)
        elif combo.type == ComboType.FIXED_AMOUNT:
            best_discount = max(best_discount, combo.discount)

    return round(best_discount, 2)

def create_receipt(current_user: Customer, distance_km: float = 0.0) -> Receipt:
    """
    **Calculates the cost of the customer's current cart and saves a receipt to storage.
    The cart is not modified. A new receipt is created each time this is called.**

    Parameters:
    *   **current_user** (Customer): the authenticated user with role *customer*
    *   **distance_km** (float): the distance in kilometers for delivery fee calculation

    Returns:
        **Receipt**: the saved receipt with full cost breakdown

    Raises:
        **HTTPException** (status_code = 400): if the cart is empty
        **HTTPException** (status_code = 404): if the cart's restaurant is not found
    """
    cart = get_cart(current_user)
    if cart.restaurant_id == 0:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    restaurant = get_restaurant_by_id(cart.restaurant_id)
    menu_items = {item.id: item for item in restaurant.menu.items}
    cart_items = {item.menu_item_id: item.qty for item in cart.cart_items}

    receipt_items = []
    subtotal = 0.0

    for cart_item in cart.cart_items:
        menu_item = menu_items.get(cart_item.menu_item_id)
        if menu_item:
            unit_price = menu_item.price
            line_total = round(unit_price * cart_item.qty, 2)
            subtotal += line_total
            receipt_items.append(ReceiptItem(
                menu_item_id=cart_item.menu_item_id,
                name=menu_item.name,
                unit_price=unit_price,
                qty=cart_item.qty,
                line_total=line_total
            ))

    subtotal = round(subtotal, 2)
    combo_discount = _calculate_combo_discount(cart_items, restaurant.menu.combos, menu_items)
    promo_subtotal = round(max(0.0, subtotal - combo_discount), 2)
    tax = round(get_tax_rate() * subtotal, 2)
    delivery_fee = restaurant.delivery_fee
    discount = combo_discount
    applied_promo_code = None

    if cart.promo_code:
        promo = validate_promo(cart.promo_code, promo_subtotal, current_user)
        delivery_fee, promo_discount = calculate_discount(promo, promo_subtotal, delivery_fee)
        discount = round(discount + promo_discount, 2)
        applied_promo_code = promo.code
        
    total = round(subtotal + tax + delivery_fee - discount, 2)

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
        discount=discount,
        promo_code=applied_promo_code,
        distance_km=distance_km,
        total=total,
    )

    receipts.append(new_receipt.model_dump())
    save_receipts(receipts)

    return new_receipt

def get_receipt(receipt_id: int) -> Receipt:
    """
    **Retrieves a saved receipt by its identifier.**

    Parameters:
        **receipt_id** (int): the identifier of the receipt to retrieve

    Returns:
        **Receipt**: the matching receipt

    Raises:
        **HTTPException** (status_code = 404): if receipt is not found
    """
    receipts = load_receipts()
    for receipt in receipts:
        if receipt.get("id") == receipt_id:
            return Receipt(**receipt)
    raise HTTPException(status_code=404, detail=f"Receipt '{receipt_id}' not found.")

def refresh_receipt(receipt_id: int, current_user: Customer) -> Receipt:
    """
    **Refreshes a receipt for when the restaurant pricing has changed since the original receipt was generated.**

    Parameters:
        **receipt_id** (int): the identifier of the receipt to refresh. used for authorization.
        **current_user** (Customer): the authenticated user who owns the receipt.

    Returns:
        **Receipt**: a newly created receipt based on the current cart state.

    Raises:
        **HTTPException** (status_code = 403): if the receipt belongs to a different user.
    """

    current_receipt = get_receipt(receipt_id)
    if current_receipt.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot refresh a receipt that belongs to another user.")

    return create_receipt(current_user, current_receipt.distance_km)
