import time
from fastapi import HTTPException, WebSocket, WebSocketException, status
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.repositories.user_repo import load_users
from app.schemas.user_schema import (
    User, 
    UserRole, 
    Customer, 
    Admin, 
    RestaurantManager, 
    DeliveryDriver, 
    ROLE_TO_CLASS
)

# tells swagger ui that the app uses bearer tokens
http_bearer = HTTPBearer()

def get_user_from_token(token: str) -> User:
    users = load_users()

    for user in users:
        if user.get("auth_token") == token:
            # check token hasnt expired
            if user.get("auth_token_expiry", 0) < time.time():
                raise HTTPException(status_code=401, detail="Session token has expired, please log in again")
            # convert role string to enum
            if isinstance(user.get("role"), str):
                user["role"] = UserRole(user["role"])
            # get user class
            user_class = ROLE_TO_CLASS[user["role"]]
            return user_class(**user)
    
    raise HTTPException(status_code=401, detail="Invalid or expired session token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> User:
    # returns matching user, or 401 if token is invalid
    token = credentials.credentials
    return get_user_from_token(token)

def require_role(required_role: UserRole):
    def role_check(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail=f"User role '{current_user.role}' does not have access to this resource")
        return current_user
    return role_check

def get_current_user_with_ws(websocket: WebSocket) -> User:
    auth = websocket.headers.get("Authorization")
    if not auth:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    token = auth.split()[1]
    return get_user_from_token(token)