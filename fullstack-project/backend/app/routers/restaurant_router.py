"""
This module defines the API routes for restaurant management.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_role
from app.schemas.user_schema import User, UserRole
from app.schemas.restaurant_schema import (
    Restaurant,
    Restaurant_Create,
    Restaurant_Details_Update,
    Restaurant_Managers_Update,
)

from app.services.restaurant_service import (
    create_restaurant,
    update_restaurant_details,
    update_restaurant_managers,
)

router = APIRouter(prefix="/restaurant", tags=["restaurant"])

# post request to create a new restaurant. Uses logged in user as the initial manager. Only managers can create restaurants.
@router.post("", response_model=Restaurant, status_code=201)
def create_restaurant_route(payload: Restaurant_Create, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    return create_restaurant(payload, current_user.id)

# put request to update restaurant details (name, city, address)
@router.put("/{restaurant_id}", response_model=Restaurant)
def update_restaurant_details_route(restaurant_id: int, payload: Restaurant_Details_Update, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_details(payload)

# put request to update restaurant managers. only managers can update restaurant managers.
@router.put("/{restaurant_id}/managers", response_model=Restaurant)
def update_restaurant_managers_route(restaurant_id: int, payload: Restaurant_Managers_Update, current_user: User = Depends(require_role(UserRole.RESTAURANT_MANAGER))):
    if restaurant_id != payload.id:
        raise HTTPException(status_code=400, detail="Restaurant ID in path and body must match")
    return update_restaurant_managers(payload)
