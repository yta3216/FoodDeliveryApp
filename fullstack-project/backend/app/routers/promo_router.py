"""
This module defines the API routes for promotional code management.
"""
from fastapi import APIRouter, Depends

from app.schemas.promo_schema import PromoApplyRequest, PromoPublic, PromoCode, PromoCode_Create, PromoCode_StatusUpdate
from app.schemas.cart_schema import Cart
from app.schemas.user_schema import Customer, User, UserRole
from app.services.user_service import get_customer
from app.services.promo_service import get_public_promos, _get_promo_by_code, create_promo, update_promo_status, get_all_promos
from app.services.cart_service import apply_promo_to_cart, remove_promo_from_cart
from app.auth import require_role

router = APIRouter(prefix="/promo", tags=["promo"])

@router.get("/all", response_model=list[PromoCode], status_code=200)
def get_all_promos_route(current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    **Returns all promo codes in the system active or public status. Admin only.**
 
    Parameters:
    *   **current_user** (User): the authenticated user with role *admin*. automatically passed as argument.
 
    Returns:
    *   **list[PromoCode]**: all promo codes including inactive and private ones
 
    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *admin*
    """
    return get_all_promos()

@router.get("", response_model=list[PromoPublic], status_code=200)
def get_promos_route():
    """
    **Returns all active, publicly visible promotional codes.**
    No authentication required — this is a public listing for customers to browse available discounts.

    Parameters: None

    Returns:
    *   **list[PromoPublic]**: all public active promo codes
    """
    return get_public_promos()


@router.post("/apply", response_model=Cart, status_code=200)
def apply_promo_route(body: PromoApplyRequest, current_user: Customer = Depends(get_customer)):
    """
    **Applies a promotional code to the customer's cart.**
    Checks that the code exists and is active. Full validation (expiry, minimum order value,
    first-order restriction) is deferred to receipt generation when the subtotal is known.
    Replaces any previously applied code — only one code is allowed per cart.

    Parameters:
    *   **body** (PromoApplyRequest): contains the promo code string to apply
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **Cart**: the updated cart with the promo code applied

    Raises:
    *   **HTTPException** (status_code = 400): if the code is inactive
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): if the promo code does not exist
    """
    promo = _get_promo_by_code(body.code)
    if not promo.is_active:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="This promo code is no longer active.")

    return apply_promo_to_cart(body.code, current_user)


@router.delete("/remove", response_model=Cart, status_code=200)
def remove_promo_route(current_user: Customer = Depends(get_customer)):
    """
    **Removes any applied promotional code from the customer's cart.**

    Parameters:
    *   **current_user** (Customer): the authenticated user with role *customer*. automatically passed as argument.

    Returns:
    *   **Cart**: the updated cart with promo code cleared

    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *customer*
    *   **HTTPException** (status_code = 404): if user is not found
    """
    return remove_promo_from_cart(current_user)

@router.post("", response_model=PromoCode, status_code=201)
def create_promo_route(body: PromoCode_Create, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    **Creates a new promotional code. Admin only.**
 
    Parameters:
    *   **body** (PromoCode_Create): the details of the promo code to create
    *   **current_user** (User): the authenticated user with role *admin*. automatically passed as argument.
 
    Returns:
    *   **PromoCode**: the newly created promo code
 
    Raises:
    *   **HTTPException** (status_code = 400): if value is invalid for the discount type, or expiry date is invalid
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *admin*
    *   **HTTPException** (status_code = 409): if a code with the same string already exists
    """
    return create_promo(body)
 
 
@router.patch("/{promo_id}/status", response_model=PromoCode, status_code=200)
def update_promo_status_route(promo_id: int, body: PromoCode_StatusUpdate, current_user: User = Depends(require_role(UserRole.ADMIN))):
    """
    **Activates or deactivates a promotional code by its identifier. Admin only.**
 
    Parameters:
    *   **promo_id** (int): the identifier of the promo code to update
    *   **body** (PromoCode_StatusUpdate): contains the new active status
    *   **current_user** (User): the authenticated user with role *admin*. automatically passed as argument.
 
    Returns:
    *   **PromoCode**: the updated promo code
 
    Raises:
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if user's role is not *admin*
    *   **HTTPException** (status_code = 404): if the promo code is not found
    """
    return update_promo_status(promo_id, body.is_active)
 