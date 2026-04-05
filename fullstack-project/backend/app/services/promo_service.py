"""
This module implements business logic for promotional code management.
Validation, discount calculation, and redemption tracking are handled here.
"""

import datetime

from fastapi import HTTPException

from app.repositories.promo_repo import load_promo_codes, save_promo_codes
from app.schemas.promo_schema import PromoCode, PromoType, PromoPublic
from app.schemas.user_schema import Customer


def get_public_promos() -> list[PromoPublic]:
    """
    **Returns all active, publicly visible promo codes.**
    Used for the customer promotions listing.

    Parameters: None

    Returns:
    *   **list[PromoPublic]**: all public, active promo codes
    """
    promos = load_promo_codes()
    return [
        PromoPublic(**promo)
        for promo in promos
        if promo.get("is_public") and promo.get("is_active")
    ]


def _get_promo_by_code(code: str) -> PromoCode:
    """
    Retrieves a promo code record by its code string.

    Parameters:
        code (str): the promo code string to look up

    Returns:
        PromoCode: the matching promo code

    Raises:
        HTTPException (status_code = 404): if no promo code matches
    """
    promos = load_promo_codes()
    for promo in promos:
        if promo.get("code", "").upper() == code.strip().upper():
            return PromoCode(**promo)
    raise HTTPException(status_code=404, detail=f"Promo code '{code}' not found.")


def validate_promo(code: str, subtotal: float, current_user: Customer) -> PromoCode:
    """
    **Validates a promo code against all business rules.**
    Checks: active status, expiry date, minimum order value, first-order restriction, and whether this customer has already used the code.

    Parameters:
        code (str): the promo code string to validate
        subtotal (float): the current cart subtotal, used for minimum order value check
        current_user (Customer): the authenticated customer applying the code

    Returns:
        PromoCode: the validated promo code

    Raises:
        HTTPException (status_code = 400): if the code fails any validation rule
        HTTPException (status_code = 404): if the code does not exist
    """
    promo = _get_promo_by_code(code)

    if not promo.is_active:
        raise HTTPException(status_code=400, detail="This promo code is no longer active.")

    if promo.expiry_date:
        expiry = datetime.date.fromisoformat(promo.expiry_date)
        if datetime.date.today() > expiry:
            raise HTTPException(status_code=400, detail="This promo code has expired.")

    if subtotal < promo.min_order_value:
        raise HTTPException(
            status_code=400,
            detail=f"A minimum order value of ${promo.min_order_value:.2f} is required for this code."
        )

    if current_user.id in promo.used_by_customer_ids:
        raise HTTPException(status_code=400, detail="You have already used this promo code.")

    if promo.is_first_order_only:
        from app.services.order_service import get_orders_for_customer
        past_orders = get_orders_for_customer(current_user)
        if len(past_orders) > 0:
            raise HTTPException(status_code=400, detail="This promo code is only valid on your first order.")

    return promo


def calculate_discount(promo: PromoCode, subtotal: float, delivery_fee: float) -> tuple[float, float]:
    """
    **Calculates the discount to apply based on promo type.**
    Returns updated delivery_fee and discount amount — the caller applies these to the receipt total.

    Parameters:
        promo (PromoCode): the validated promo code to apply
        subtotal (float): the order subtotal before tax and delivery
        delivery_fee (float): the current delivery fee

    Returns:
        tuple[float, float]: (updated_delivery_fee, discount_amount)
        - updated_delivery_fee: 0.0 for free_delivery, unchanged otherwise
        - discount_amount: the dollar value being deducted from the total
    """
    if promo.type == PromoType.FREE_DELIVERY:
        return 0.0, round(delivery_fee, 2)

    if promo.type == PromoType.FIXED_AMOUNT:
        discount = min(promo.value, subtotal)
        return delivery_fee, round(discount, 2)

    if promo.type == PromoType.PERCENTAGE:
        discount = round(subtotal * (promo.value / 100), 2)
        return delivery_fee, discount

    return delivery_fee, 0.0


def redeem_promo(code: str, customer_id: str) -> None:
    """
    **Records a promo code redemption after a successful payment.**
    Increments usage count and adds the customer to the used_by list.
    Called by payment_service after checkout succeeds.

    Parameters:
        code (str): the promo code string that was redeemed
        customer_id (str): the id of the customer who redeemed it

    Returns:
        None
    """
    promos = load_promo_codes()
    for promo in promos:
        if promo.get("code", "").upper() == code.strip().upper():
            promo["usage_count"] = promo.get("usage_count", 0) + 1
            used_by = promo.get("used_by_customer_ids", [])
            if customer_id not in used_by:
                used_by.append(customer_id)
            promo["used_by_customer_ids"] = used_by
            save_promo_codes(promos)
            return


def get_first_order_promo() -> PromoCode | None:
    """
    **Returns the active first-order-only promo code if one exists.**
    Used during checkout to auto-apply a welcome discount for new customers on first order.

    Parameters: None

    Returns:
    *   **PromoCode | None**: the first active first-order promo found, or None
    """
    promos = load_promo_codes()
    for promo in promos:
        if promo.get("is_first_order_only") and promo.get("is_active"):
            return PromoCode(**promo)
    return None