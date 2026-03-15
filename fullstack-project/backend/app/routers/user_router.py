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
    **Creates a new user in the system.**

    Parameters:
    *   **payload** (User_Create): the data for the new user

    Returns:
    *   **UserPublic**: the newly created user

    Raises:
    *    **HTTPException** (status_code = 409): if generated ID matches an existing ID. extremely unlikely.
    """
    return create_user(payload)

@router.post("/login", response_model=LoginResponse)
def login_user_route(payload: LoginRequest):
    """
    **Logs a user into the system.**

    Parameters:
    *   **payload** (LoginRequest): the provided email and password in the login attempt

    Returns:
    *   **LoginResponse**: the user's details inluding their login token

    Raises:
    *    **HTTPException** (status_code = 401): if email/password pair is not found in users.json
    """
    return login_user(payload.email, payload.password)

@router.get("/{user_id}", response_model=UserPublic)
def get_user_route(user_id: str, current_user: User = Depends(get_current_user)):
    """
    **Retrieves the data of a user. Admin accounts can access any user; other users can only access their own account.**

    Parameters:
    *   **user_id** (str): the identifier of the user to be retrieved
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **UserPublic**: the requested user's data

    Raises:
    *   **HTTPException** (status_code = 403): user does not have role *admin* and their id does not match user_id in URL
    *   **HTTPException** (status_code = 404): user_id not found in users.json
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this user's details")
    return get_user_by_id(user_id)

@router.put("/{user_id}", response_model=UserPublic)
def update_user_route(user_id: str, payload: User_Update, current_user: User = Depends(get_current_user)):
    """
    **Updates the data of a user. Admin accounts can access any user; other users can only access their own account.**

    Parameters:
    *   **user_id** (str): the identifier of the user to be updated
    *   **payload** (User_Update): the updated user account details
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **User_Public**: the newly updated user details

    Raises:
    *   **HTTPException** (status_code = 403): user does not have role *admin* and their id does not match user_id in URL
    *   **HTTPException** (status_code = 404): if user_id is not found in users.json
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to edit this user's details")
    return update_user(user_id, payload)

@router.post("/password-reset/request")
def password_reset_request(payload: Password_Reset_Request):
    """
    **Requests a password reset link for a non-logged in user. Does not return any data indicating if email exists or not.**
    *Reset links are printed to the terminal to simulate an email for now.*

    Parameters:
    *   **payload** (Password_Reset_Request): the email of the account to be updated
    
    Returns: None
    """
    reset_password_request(payload.email)
    return {"detail": "If the email exists, a password reset link has been sent."}

@router.post("/reset-password")
def perform_reset_password(payload: Password_Reset):
    """
    **Resets the password of a user who has recently requested a password reset.**

    Parameters:
    *   **payload** (Password_Reset): the password reset token and desired new password

    Returns:
    *   **dict[str, str]: a message stating that password reset was successful

    Raises:
    *   **HTTPException** (status_code = 400): if user's reset token is invalid or expired

    """
    reset_password(payload.new_password, payload.reset_token)
    return {"detail": "Password reset successful."}

@router.put("/{user_id}/password")
def update_password_logged_in(user_id: str, payload: Password_Update_When_Logged_In, current_user: User = Depends(get_current_user)):
    """
    **Resets the password of a logged-in user.**

    Parameters:
    *   **user_id** (str): the identifier for the account to be updated. must match the logged in user's id
    *   **payload** (Password_Reset): the password reset token and desired new password
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **dict[str, str]: a message stating that the user's password was updated

    Raises:
    *   **HTTPException (status_code = 403): if current user's id does not match user_id in URL
    *   **HTTPException** (status_code = 400): if password is incorrect
    *   **HTTPException** (status_code = 404): if user_id is not found in users.json
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to change this user's password")
    update_password_when_logged_in(user_id, payload.old_password, payload.new_password)
    return {"detail": "Password updated."}

@router.get("/{user_id}/notifications", response_model=list[Notification_Response])
def get_notifications_route(user_id: str, current_user: User = Depends(get_current_user)):
    """
    **Retrieves all notifications ever sent to the logged-in user.**

    Parameters:
    *   **user_id** (str): the identifier of the account to retrieve notifications for. must match the logged in user's id
    *   **current_user** (User): the authenticated user. automatically passed as argument.

    Returns:
    *   **list[Notification_Response]**: a list of the notifications associated with the logged-in user

    Raises:
    *   **HTTPException (status_code = 403): if current user's id does not match user_id in URL
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to view this user's notifications")
    return get_notifications(user_id)

# TODO: get single notification

# TODO: mark notification as read