""" This module implements business logic for cart management. """

from fastapi import HTTPException

from app.repositories.user_repo import load_users, save_users
from app.services.restaurant_service import get_restaurant_by_id
from app.schemas.restaurant_schema import Restaurant
from app.schemas.user_schema import Customer
from app.schemas.cart_schema import (
    CartItem,
    CartItem_Update,
    CartItem_Create,
    Cart
)


def _restaurant_has_menu_item(restaurant: Restaurant, menu_item_id: int) -> bool:
    """
    Checks whether a restaurant menu contains the given item id.

    Parameters:
        restaurant (Restaurant): the restaurant whose menu is being checked for the item
        menu_item_id (int): the menu item id being checked for in the restaurant's menu

    Returns:
        bool: true if the restaurant's menu contains the item, false otherwise
    """
    return any(menu_item.id == menu_item_id for menu_item in restaurant.menu.items)

def update_cart_restaurant(restaurant_id: int, current_user: Customer) -> Cart:
    """
    Updates the restaurant associated with a user's cart, used when they want to change the restaurant they're ordering from.
    The cart is emptied if the new restaurant is different than the old one, as the items are no longer applicable.

    Parameters:
        restaurant_id (int): the identifier of the restaurant to be attached to the cart
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        Cart: the cart with updated restaurant ID.

    Raises:
        HTTPException (status_code = 404): current_user's user_id not found in users.json
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            if user["cart"]["restaurant_id"] == restaurant_id:
                return Cart(**user["cart"])
            user["cart"] = Cart(restaurant_id=restaurant_id).model_dump()
            save_users(users)
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def get_cart(current_user: Customer) -> Cart:
    """
    Retrieves the provided customer's cart.

    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        Cart: the customer's cart

    Raises:
        HTTPException (status_code = 404): current_user's user_id not found in users.json
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def empty_cart(current_user: Customer) -> None:
    """
    Empties the customer's cart by restoring it to default values.

    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns: None

    Raises:
        HTTPException (status_code = 404): current_user's user_id not found in users.json
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"] = Cart().model_dump()
            save_users(users)
            return None
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def apply_promo_to_cart(code: str, current_user: Customer) -> Cart:
    """
    Saves a promo code string to the customer's cart.
    Replaces any previously applied promo code - only one code is allowed per cart.
 
    Parameters:
        code (str): the promo code to apply
        current_user (Customer): the current logged-in user. must have role "customer"
 
    Returns:
        Cart: the updated cart with promo code applied
 
    Raises:
        HTTPException (status_code = 404): current_user's user_id not found in users.json
    """
    from app.services.promo_service import get_promo_by_code
    promo = get_promo_by_code(code)
    if not promo.is_active:
        raise HTTPException(status_code=400, detail="This promo code is no longer active.")
    
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"]["promo_code"] = promo.code
            save_users(users)
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def remove_promo_from_cart(current_user: Customer) -> Cart:
    """
    Removes any applied promo code from the customer's cart.
 
    Parameters:
        current_user (Customer): the current logged-in user. must have role "customer"
 
    Returns:
        Cart: the updated cart with promo code cleared
 
    Raises:
        HTTPException (status_code = 404): current_user's user_id not found in users.json
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"]["promo_code"] = None
            save_users(users)
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def create_cart_item(payload: CartItem_Create, current_user: Customer) -> CartItem:
    """
    Adds a new item to the customer's cart.

    Parameters:
        payload (CartItem_Create): the item to be added to the cart
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        CartItem: the item added to cart

    Raises:
        HTTPException (status_code = 400): if user's cart has no associated restaurant
        HTTPException (status_code = 404): current user's cart's restaurant_id not found in restaurants.json,
                                           or current user's id not found in users.json,
                                           or new cart item's id not found in restaurant's menu
    """
    users = load_users()
    restaurant_id = current_user.cart.restaurant_id

    if restaurant_id == 0:
        raise HTTPException(400, detail=f"User '{current_user.id}' cart has no associated restaurant")

    restaurant = get_restaurant_by_id(restaurant_id)
    if _restaurant_has_menu_item(restaurant, payload.menu_item_id):
        for user in users:
            if user.get("id") == current_user.id:
                new_item = payload.model_dump()
                user["cart"]["cart_items"].append(new_item)
                save_users(users)
                return CartItem(**new_item)
        raise HTTPException(404, detail=f"User '{current_user.id}' not found")
    raise HTTPException(404, detail=f"Item {payload.menu_item_id} not found in restaurant {restaurant_id} menu")

def get_cart_item(item_id: int, current_user: Customer) -> CartItem:
    """
    Retrieve an item from the customer's cart by its identifier.

    Parameters:
        item_id (int): the item's identifier
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        CartItem: the item from the customer's cart with matching item_id

    Raises:
        HTTPException (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    return CartItem(**item)
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def update_cart_item(item_id: int, payload: CartItem_Update, current_user: Customer) -> CartItem:
    """
    Updates the quantity of an item in the customer's cart.

    Parameters:
        item_id (int): the item's identifier
        payload (CartItem_Update): the updated item quantity
        current_user (Customer): the current logged-in user. must have role "customer"
    
    Returns:
        CartItem: the updated item from the customer's cart

    Raises:
        HTTPException (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    item["qty"] = payload.new_qty
                    save_users(users)
                    return CartItem(**item)
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

def delete_cart_item(item_id: int, current_user: Customer) -> CartItem:
    """
    Removes an item from the provided customer's cart.

    Parameters:
        item_id (int): the identifier of the item to be removed from the customer's cart
        current_user (Customer): the current logged-in user. must have role "customer"

    Returns:
        CartItem: the item removed from customer's cart

    Raises:
        HTTPException (status_code = 404): current user's id not found in users.json or cart item id not found in user's cart
    """
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    user["cart"]["cart_items"].remove(item)
                    save_users(users)
                    return CartItem(**item)
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")
