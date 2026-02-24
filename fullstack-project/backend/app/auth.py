import time
from fastapi import Header, HTTPException
from app.repositories.user_repo import load_users
from app.schemas.user_schema import User, UserRole


def get_current_user(authorization: str = Header(...)) -> User:
# Returns  matching user, or 401 if token is invalid
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.removeprefix("Bearer ").strip()
    users = load_users()

    for user in users:
        if user.get("auth_token") == token:
            # check token hasnt expired
            if user.get("auth_token_expiry", 0) < time.time():
                raise HTTPException(status_code=401, detail="Session token has expired, please log in again")
            # convert role string to enum
            if isinstance(user.get("role"), str):
                user["role"] = UserRole(user["role"])
            return User(**user)
    
    raise HTTPException(status_code=401, detail="Invalid or expired session token")