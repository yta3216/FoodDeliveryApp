""" This module implements business logic for cart management. """

from fastapi import HTTPException

from app.repositories.user_repo import load_users, save_users
from app.services.restaurant_service import get_restaurant_by_id
from app.schemas.user_schema import Customer
from app.schemas.cart_schema import (
    CartItem,
    CartItem_Update,
    CartItem_Create,
    Cart
)
from app.schemas.order_schema import (
    Order,
    OrderItem,
)

def calculate_cart_total(cart: Cart) -> float:
    restaurant = get_restaurant_by_id(cart.restaurant_id)
    menu_items = {item["id"]: item for item in restaurant["menu"]["items"]}
    total = 0.0
    for cart_item in cart.cart_items:
        menu_item = menu_items.get(cart_item.menu_item_id)
        if menu_item:
            total += menu_item.get("price", 0.0) * cart_item.qty
    return total

# transition from cart to order. 
def create_order_from_cart(current_user: Customer) -> Order:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            cart = user["cart"]
            if cart["restaurant_id"] == 0 or len(cart["cart_items"]) == 0:
                raise HTTPException(204, detail=f"Cart is empty")
            # creates a new order with the same restaurant id and items as the cart
            new_order = Order(
                restaurant_id=cart["restaurant_id"],
                items=[OrderItem(menu_item_id=item["menu_item_id"], qty=item["qty"]) for item in cart["cart_items"]]
            )
            empty_cart(current_user) # empties the cart after creating the order
            save_users(users)
            return new_order
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Set restaurant id
def update_cart_restaurant(restaurant_id: int, current_user: Customer) -> Cart:
    # update user cart
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            if user["cart"]["restaurant_id"] == restaurant_id:
                return user["cart"] # restaurant is unchanged, leave old items there
            # we just create a new empty card with given id, as old items won't be applicable
            user["cart"] = Cart(restaurant_id=restaurant_id).model_dump()
            save_users(users)
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# get the users cart
def get_cart(current_user: Customer) -> Cart:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            return Cart(**user["cart"])
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# empty the cart (by resetting to default values)
def empty_cart(current_user: Customer) -> None:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["cart"] = Cart().model_dump()
            save_users(users)
            return None
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Create new cart item in cart
def create_cart_item(payload: CartItem_Create, current_user: Customer) -> CartItem:
    users = load_users()
    restaurant_id = current_user.cart.restaurant_id
    # if restaurant associated with cart hasn't been set
    if restaurant_id == 0:
        raise HTTPException(204, detail=f"User '{current_user.id}' cart has no associated restaurant")
    # if it is set, obtain the restaurant and confirm item exists in its menu
    restaurant = get_restaurant_by_id(restaurant_id)
    if any(menu_item["id"] == payload.menu_item_id for menu_item in restaurant["menu"]["items"]):
        # add the item to user's cart and save
        for user in users:
            if user.get("id") == current_user.id:
                new_item = payload.model_dump()
                user["cart"]["cart_items"].append(new_item)
                save_users(users)
                return CartItem(**new_item)
        raise HTTPException(404, detail=f"User '{current_user.id}' not found")
    raise HTTPException(404, detail=f"Item {payload.menu_item_id} not found in restaurant {restaurant_id} menu")

# get an item in cart
def get_cart_item(item_id: int, current_user: Customer) -> CartItem:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    return CartItem(**item)
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
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
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")

# Delete item from cart
def delete_cart_item(item_id: int, current_user: Customer) -> CartItem:
    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            for item in current_user["cart"]["cart_items"]:
                if item.get("menu_item_id") == item_id:
                    current_user["cart"]["cart_items"].remove(item)
                    save_users(users)
                    return CartItem(item.model_dump())
            raise HTTPException(404, detail=f"Item '{item_id}' not found in user '{current_user.id}' cart")
    raise HTTPException(404, detail=f"User '{current_user.id}' not found")
