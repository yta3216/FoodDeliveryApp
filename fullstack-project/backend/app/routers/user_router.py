from typing import List
from fastapi import APIRouter, status, Query
from app.schemas.user_schema import (
    User,
    User_Create,
    User_Update,
    LoginRequest,
    LoginResponse,
    Password_Reset_Request,
    Password_Reset,
    Password_Update_When_Logged_In,
)
from app.services.user_service import (
    create_user,
    get_user_by_id,
    login_user,
    reset_password_request,
    reset_password,
    update_password_when_logged_in,
)

router = APIRouter(prefix="/user", tags=["user"])

# post request to create a new user
# we use the User_Create schema because we dont want the client to send an id
@router.post("", response_model=User, status_code=201)
def create_user_route(payload: User_Create):
    return create_user(payload)

# login with email and password
@router.post("/login", response_model=LoginResponse)
def login_user_route(payload: LoginRequest):
    return login_user(payload.email, payload.password)

# get request to retrieve a user by id
@router.get("/{user_id}", response_model=User)
def get_user_route(user_id: str):
    return get_user_by_id(user_id)

@router.put("/{user_id}")
def update_user_route(user_id: str, payload: User_Update):
    # placeholder - keep existing behavior in repo
    raise NotImplementedError()

# password reset request - non-logged in user wants to reset password.
@router.post("/password-reset/request")
def password_reset_request(payload: Password_Reset_Request):
    reset_password_request(payload.email)
    return {"detail": "If the email exists, a password reset link has been sent."}

# once user has received reset token, they can use it to reset their password.
@router.post("/reset-password")
def perform_reset_password(payload: Password_Reset):
    reset_password(payload.new_password, payload.reset_token)
    return {"detail": "Password reset successful."}

# logged in user wants to update their password, so they provide old and new password.
@router.put("/{user_id}/password")
def update_password_logged_in(user_id: str, payload: Password_Update_When_Logged_In):
    update_password_when_logged_in(user_id, payload.old_password, payload.new_password)
    return {"detail": "Password updated."}
