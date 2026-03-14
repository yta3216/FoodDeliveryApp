""" 
This module defines the API routes for user management.
"""

from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas.notification_schema import Notification_Response
from app.schemas.user_schema import (
    User,
    UserPublic,
    User_Create,
    User_Update,
    LoginRequest,
    LoginResponse,
    Password_Reset_Request,
    Password_Reset,
    Password_Update_When_Logged_In,
    UserRole,
)
from app.services.user_service import (
    create_user,
    get_user_by_id,
    login_user,
    reset_password_request,
    reset_password,
    update_password_when_logged_in,
    update_user,
    get_notifications
)
from app.auth import get_current_user

router = APIRouter(prefix="/user", tags=["user"])

@router.post("", response_model=UserPublic, status_code=201)
def create_user_route(payload: User_Create):
    """
    Creates a new user in the system.

    Parameters:
    *   **payload** (User_Create): the data for the new user

    Returns:
    *   **UserPublic**: the newly created user
    """
    return create_user(payload)

@router.post("/login", response_model=LoginResponse)
def login_user_route(payload: LoginRequest):
    """
    Logs a user into the system.

    Parameters:
    *   **payload** (LoginRequest): the provided email and password in the login attempt

    Returns:
    *   **LoginResponse**: the user's details inluding their login token
    """
    return login_user(payload.email, payload.password)

@router.get("/{user_id}", response_model=UserPublic)
def get_user_route(user_id: str, current_user: User = Depends(get_current_user)):
    """
    Retrieves the data of any user
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this user's details")
    return get_user_by_id(user_id)

# update user details - users can only update their own account
@router.put("/{user_id}", response_model=UserPublic)
def update_user_route(user_id: str, payload: User_Update, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this user's details")
    return update_user(user_id, payload)

# password reset request - non-logged in user wants to reset password
@router.post("/password-reset/request")
def password_reset_request(payload: Password_Reset_Request):
    reset_password_request(payload.email)
    return {"detail": "If the email exists, a password reset link has been sent."}

# once user has received reset token, they can use it to reset their password
@router.post("/reset-password")
def perform_reset_password(payload: Password_Reset):
    reset_password(payload.new_password, payload.reset_token)
    return {"detail": "Password reset successful."}

# logged in user wants to update their password
@router.put("/{user_id}/password")
def update_password_logged_in(user_id: str, payload: Password_Update_When_Logged_In, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to change this user's password")
    update_password_when_logged_in(user_id, payload.old_password, payload.new_password)
    return {"detail": "Password updated."}

# logged in user wants to retrieve their notifications.
@router.get("/{user_id}/notifications", response_model=list[Notification_Response])
def get_notifications_route(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this user's notifications")
    return get_notifications(user_id)

# TODO: get single notification

# TODO: mark notification as read