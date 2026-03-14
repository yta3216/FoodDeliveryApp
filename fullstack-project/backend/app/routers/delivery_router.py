from fastapi import APIRouter, Depends
from app.schemas.delivery_schema import Delivery
from app.schemas.user_schema import User, UserRole
from app.auth import require_role
from app.services.delivery_service import (
    start_delivery,
    complete_delivery,
    get_delivery_by_order,
    check_waiting_orders,
)
from app.repositories.user_repo import load_users, save_users
from app.auth import get_current_user

router = APIRouter(prefix="/delivery", tags=["delivery"])


# driver updates their own status (available, unavailable)
# if they set to available, system checks for waiting orders
@router.patch("/status", status_code=200)
def update_driver_status_route(
    status: str,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    if status not in ("available", "unavailable"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="status must be available or unavailable")

    users = load_users()
    for user in users:
        if user.get("id") == current_user.id:
            user["driver_status"] = status
            break
    save_users(users)

    # if driver just became available, check for any waiting orders
    if status == "available":
        updated_user = next(u for u in users if u.get("id") == current_user.id)
        check_waiting_orders(updated_user)

    return {"message": f"status updated to {status}"}


# driver marks order as delivering: starts the timer and calculates eta
@router.patch("/{order_id}/start", response_model=Delivery, status_code=200)
def start_delivery_route(
    order_id: int,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    return start_delivery(order_id=order_id, driver_id=current_user.id)


# driver marks order as delivered: stops the timer and records actual time
@router.patch("/{order_id}/complete", response_model=Delivery, status_code=200)
async def complete_delivery_route(
    order_id: int,
    current_user: User = Depends(require_role(UserRole.DELIVERY_DRIVER))
):
    from app.repositories.order_repo import load_orders, save_orders
    from app.services.order_service import send_status_notification

    delivery = complete_delivery(order_id=order_id, driver_id=current_user.id)

    # update order status to delivered
    orders = load_orders()
    for order in orders:
        if order.get("id") == order_id:
            order["status"] = "delivered"
            save_orders(orders)
            await send_status_notification(order)
            break

    return delivery


# customer views delivery info for their order
@router.get("/{order_id}", response_model=Delivery, status_code=200)
def get_delivery_route(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    return get_delivery_by_order(order_id=order_id)