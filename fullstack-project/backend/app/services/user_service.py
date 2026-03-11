"""This module implements business logic for user management."""

import secrets
import time
from typing import Any
import uuid
from fastapi import HTTPException, Depends
from app.auth import require_role
from app.repositories.user_repo import load_users, save_users
from app.schemas.notification_schema import Notification_Response
from app.schemas.user_schema import (
    User, 
    User_Create,
    UserRole,
    LoginResponse,
    UserPublic,
    User_Update,
    Customer,
    ROLE_TO_CLASS
)

RESET_TOKEN_EXPIRY = 900  # 15 minutes before password reset token expires
SESSION_TOKEN_EXPIRY = 86400  # 24 hours before session token expires


def create_user(payload: User_Create) -> User:
    users = load_users()
    new_id = str(uuid.uuid4()) # generate unique ID for the new user
    if any(user.get("id") == new_id for user in users):
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    
    # use appropriate constructor based on user class.
    user_class = ROLE_TO_CLASS[payload.role]

    new_user = user_class(
        id = new_id,
        email = payload.email.strip(),
        password = payload.password.strip(),
        name = payload.name.strip(),
        age = payload.age,
        gender = payload.gender.strip(),
        reset_token = None,
        reset_token_expiry = None
    )

    users.append(new_user.model_dump())
    save_users(users)
    return new_user

# get User object by user id
def get_user_by_id(user_id: str) -> User:
    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            if isinstance(user.get("role"), str): # ensure role is properly converted to UserRole enum
                user["role"] = UserRole(user["role"]) 
            return User(**user)
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

# log in user
def login_user(email: str, password: str) -> LoginResponse:
    users = load_users()
    email = email.strip()
    password = password.strip()
    for user in users:
        if user.get("email") == email:
            if user.get("password") != password:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            token = secrets.token_urlsafe(32) # generate a secure session token
            user["auth_token"] = token
            user["auth_token_expiry"] = time.time() + SESSION_TOKEN_EXPIRY
            save_users(users)
            role = UserRole(user["role"]) if isinstance(user.get("role"), str) else user["role"] # convert role to enum
            return LoginResponse(
                token = token,
                user_id= user.get("id"),
                email = user.get("email"),
                role= role,
                age= user.get("age"),
                gender= user.get("gender"),
                name=user.get("name"),
            )
    raise HTTPException(status_code=401, detail="Invalid email or password")

# Used when a non-logged in user has forgotten their password and needs to reset it.
def reset_password_request(user_email: str) -> None:
    users = load_users()
    for user in users:
        if user.get("email") == user_email:
            token = secrets.token_urlsafe(32)  # generate a secure random token
            user["reset_token"] = token
            user["reset_token_expiry"] = time.time() + RESET_TOKEN_EXPIRY  # set expiry timestamp
            save_users(users)

            # simulate sending email by printing the reset link to the console
            print(f"\nPassword reset link:")
            print(f"http://localhost:8000/user/reset-password?token={token}\n")

            return None
    return None  # don't want to reveal whether the email exists or not, so we do not return any information here.

# Used when a non-logged in user has requested a password reset and has input their new password.
def reset_password(new_password: str, reset_token: str) -> None:
    users = load_users()
    for user in users:
        if user.get("reset_token") == reset_token:
            if user.get("reset_token_expiry", 0) < time.time():
                raise HTTPException(status_code=400, detail="Reset token has expired")
            # update user password and clear reset token and expiry
            user["password"] = new_password.strip()
            user["reset_token"] = None
            user["reset_token_expiry"] = None
            save_users(users)
            return None
    raise HTTPException(status_code=400, detail="Invalid reset token")

# Used when a logged in user wants to change their password.
def update_password_when_logged_in(user_id: str, old_password: str, new_password: str) -> None:
    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            if user.get("password") != old_password:
                raise HTTPException(status_code=400, detail="Old password is incorrect")
            user["password"] = new_password.strip()
            save_users(users)
            return None
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")


def update_user(user_id: str, payload: User_Update) -> UserPublic:
    users = load_users()
    for idx, user in enumerate(users):
        if user.get("id") == user_id:
            # only update allowed fields, role and password are not changeable here
            user["name"] = payload.name.strip()
            user["email"] = payload.email.strip()
            user["age"] = payload.age
            user["gender"] = payload.gender.strip()
            users[idx] = user
            save_users(users)
            role = UserRole(user["role"]) if isinstance(user.get("role"), str) else user["role"]
            return UserPublic(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                age=user["age"],
                gender=user["gender"],
                role=role
            )
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

# load notifications for the provided user.
def get_notifications(user_id: str) -> Notification_Response:
    # load all. reading notifications will be implemented later probably

    # maybe do schema
    """
    class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    time: str
    type: str
    """

# this function authenticates the user and confirms that they are of customer type
def get_customer(customer: Customer = Depends(require_role(UserRole.CUSTOMER))) -> Customer:
    return customer
