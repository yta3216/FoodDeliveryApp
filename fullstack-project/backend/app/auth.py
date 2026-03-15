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
    """
    Authenticates and retrives a user based on their authentication token.

    Parameters:
        token (str): the user's authentication token

    Returns:
        User: the logged-in user's data
    
    Raises:
        HTTPException (status_code = 401): if user's token is invalid or expired
    """
    users = load_users()

    for user in users:
        if user.get("auth_token") == token:
            if user.get("auth_token_expiry", 0) < time.time():
                raise HTTPException(status_code=401, detail="Session token has expired, please log in again")

            if isinstance(user.get("role"), str):
                user["role"] = UserRole(user["role"])

            user_class = ROLE_TO_CLASS[user["role"]]
            return user_class(**user)
    
    raise HTTPException(status_code=401, detail="Invalid or expired session token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> User:
    """
    Authenticates and retrieves the user currently using the system.

    Parameters:
        credentials (HTTPAuthorizationCredentials): the current user's authorization credentials. automatically passed as an argument
    
    Returns:
        User: the authenticated user's details, corresponsing to the provided token

    Raises:
        HTTPException (status_code = 401): if user's token is invalid or expired
    """
    token = credentials.credentials
    return get_user_from_token(token)

def require_role(required_role: UserRole):
    """
    Authenticates and retrieves the current user, and confirms they are of the correct role.

    Parameters:
        required_role (UserRole): the role that this user must posess
    
    Returns:
        role_check: a FastAPI dependency function which ultimately returns the current user

    Raises:
        HTTPException (status_code = 401): if user's token is invalid or expired
        HTTPException (status_code = 403): if user's role does not match the requested role
    """
    def role_check(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail=f"User role '{current_user.role}' does not have access to this resource")
        return current_user
    return role_check

def get_current_user_with_ws(websocket: WebSocket) -> User:
    """
    Authenticates and retrives the current user from a WebSocket Connection.

    Parameters:
        websocket (WebSocket): the WebSocket connection object containing the user's authorization token in headers
    
    Returns:
        User: the authenticated user's details
    
    Raises:
        WebSocketException (code = WS_1008_POLICY_VIOLATION): if the Authorization header is missing from the WebSocket request
        HTTPException (status_code = 401): if user's token is invalid or expired
    """
    auth = websocket.headers.get("Authorization")
    if not auth:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    token = auth.split()[1]
    return get_user_from_token(token)