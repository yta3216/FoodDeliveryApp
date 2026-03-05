""" This module implements business logic for cart management. """

from typing import List

from fastapi import HTTPException, Depends

from .user_service import get_user_by_id
from app.auth import require_role
from app.services.user_service import load_users, save_users
from app.schemas.user_schema import Customer, UserRole
from app.schemas.cart_schema import (
    CartItem,
    CartItem_Update,
    CartItem_Create,
    Cart
)

# Set menu id
def update_cart_menu(menu_id: int, current_user: Customer) -> Cart:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"] = Cart() # reset cart first to remove items from previous menu
            user["cart"]["id"] = menu_id
            save_users(users)
            return Cart(**user.cart)
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# empty the cart (by resetting to default values)
def empty_cart(current_user: Customer) -> None:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"] = Cart()
            save_users(users)
            return None
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Create new cart item in cart
def create_cart_item(payload: CartItem_Create, current_user: Customer) -> CartItem:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            new_item = payload.model_dump()
            user["cart"]["cart_items"].append(new_item)
            save_users(users)
            return CartItem(**new_item)
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Update qty of an item in cart
def update_cart_item(item_id: int, payload: CartItem_Update, current_user: Customer) -> CartItem:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    item["qty"] = payload.new_qty
                    save_users(users)
                    return CartItem(**item)
            raise HTTPException(404, detail=f"Item '{payload.menu_item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Delete item from cart
def delete_cart_item(item_id: int, current_user: Customer) -> CartItem:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in current_user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    old_item = item
                    current_user["cart"]["cart_items"].remove(item)
                    save_users(users)
                    return CartItem(item.model_dump())
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")
