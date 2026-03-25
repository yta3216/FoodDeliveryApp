"""This module implements business logic for user management."""

import secrets
import time
import uuid
from fastapi import HTTPException, Depends
from app.auth import require_role
from app.repositories.user_repo import load_users, save_users
from app.repositories.notification_repo import load_notifications
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
from app.services.config_service import get_reset_token_expiry_default, get_session_token_expiry_default

RESET_TOKEN_EXPIRY, SESSION_TOKEN_EXPIRY = get_reset_token_expiry_default(), get_session_token_expiry_default()

def create_user(payload: User_Create) -> User:
    """
    Creates a new user with unique id and saves to users.json. Uses appropriate subclass constructor based on role.

    Parameters:
        payload (User_Create): the details of the user to be created
    
    Returns:
        User: the newly created user

    Raises:
        HTTPException (status_code = 409): if generated ID matches an existing ID, or if email exists already.
    """
    users = load_users()
    new_id = str(uuid.uuid4())
    new_email = payload.email.strip()
    for user in users:
        if user.get("id") == new_id:
            raise HTTPException(status_code=409, detail="ID collision; retry.")
        if user.get("email") == new_email:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
    
    user_class = ROLE_TO_CLASS[payload.role]

    new_user = user_class(
        id = new_id,
        email = new_email,
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

def get_user_by_id(user_id: str) -> User:
    """
    Retrieves a user by the provided user id.

    Parameters:
        user_id (str): the identifier of the user to be retrieved
    
    Returns:
        User: the details of the user with matching id

    Raises:
        HTTPException (status_code = 404): user_id not found in users.json
    """
    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            if isinstance(user.get("role"), str):
                user["role"] = UserRole(user["role"]) 
            return User(**user)
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")

def login_user(email: str, password: str) -> LoginResponse:
    """
    Authenticates and logs in the user based on the provided email and password.

    Parameters:
        email (str): user's email
        password (str): user's password
    
    Returns:
        LoginReponse: the user's details post-login

    Raises:
        HTTPException (status_code = 401): if email/password pair is not found in users.json
    """
    users = load_users()
    email = email.strip()
    password = password.strip()
    for user in users:
        if user.get("email") == email:
            if user.get("password") != password:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            token = secrets.token_urlsafe(32)
            user["auth_token"] = token
            user["auth_token_expiry"] = time.time() + SESSION_TOKEN_EXPIRY
            save_users(users)
            role = UserRole(user["role"]) if isinstance(user.get("role"), str) else user["role"]
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

def reset_password_request(user_email: str) -> None:
    """
    Requests a password reset for a given email, used when the user has forgotten their password.
    A password reset token is attached to the account and will expire after a set amount of time. 
    A password reset link is printed to the terminal to simulate the link being sent via email.
    Nothing is returned for security purposes, to not reveal the existence of the email in the db.

    Parameters:
        user_email (str): the email of the user who wishes to reset their password

    Returns: None
    """
    users = load_users()
    for user in users:
        if user.get("email") == user_email:
            token = secrets.token_urlsafe(32)
            user["reset_token"] = token
            user["reset_token_expiry"] = time.time() + RESET_TOKEN_EXPIRY
            save_users(users)

            print(f"\nPassword reset link:")
            print(f"http://localhost:8000/user/reset-password?token={token}\n")

            return None
    return None

def reset_password(new_password: str, reset_token: str) -> None:
    """
    Resets the password for a user who has a valid token from a password reset request.
    Reset token is cleared after password is reset.

    Parameters:
        new_password (str): the new password
        reset_token (str): the reset token obtained from the password reset request

    Returns: None

    Raises:
        HTTPException (status_code = 400): if user's reset token is invalid or expired
    """
    users = load_users()
    for user in users:
        if user.get("reset_token") == reset_token:
            if user.get("reset_token_expiry", 0) < time.time():
                raise HTTPException(status_code=400, detail="Reset token has expired")

            user["password"] = new_password.strip()
            user["reset_token"] = None
            user["reset_token_expiry"] = None
            save_users(users)
            return None
    raise HTTPException(status_code=400, detail="Invalid reset token")

def update_password_when_logged_in(user_id: str, old_password: str, new_password: str) -> None:
    """
    Updates the password of a user who remembers their existing password.

    Parameters:
        user_id (str): the identifier of the user account whose password will be updated
        old_password (str): the user's current password
        new_password (str): the user's requested new password

    Returns: None

    Raises:
        HTTPException (status_code = 400): if password is incorrect
        HTTPException (status_code = 404): if user_id is not found in users.json
    """
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
    """
    Updates a user's account details.

    Parameters:
        user_id (str): the identifier of the user account to be updated
        payload (User_Update): the requested updates to user details

    Returns:
        UserPublic: the user's updated details with password hidden for security

    Raises:
        HTTPException (status_code = 404): if user_id is not found in users.json
    """
    users = load_users()
    for idx, user in enumerate(users):
        if user.get("id") == user_id:

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

def get_notifications(user_id: str) -> list[Notification_Response]:
    """
    Retrieves all notifications in notifications.json with the provided user as a recipient.

    Parameters:
        user_id (str): the identifier for the user whose notifications will be retrieved

    Returns:
        list[Notification_Response]: the user's notifications
    """
    notifs = load_notifications()
    user_notifs = [Notification_Response]
    for notif in notifs:
        if user_id in notif["user_ids"]:
            user_notifs.append(notif)
    return user_notifs

def get_customer(customer: Customer = Depends(require_role(UserRole.CUSTOMER))) -> Customer:
    """
    Authenticates the user and confirms that they are of customer type.

    Parameters:
        customer (Customer): the currently logged-in user, must have role "customer". automatically passed as an argument

    Returns:   
        Customer: the logged-in customer's data

    Raises:
        HTTPException (status_code = 401): if user's token is invalid or expired
        HTTPException (status_code = 403): if user's role does not match the requested role
    """
    return customer
