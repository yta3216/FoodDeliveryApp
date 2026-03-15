"""
This module defines the endpoints for real-time updates from the server.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException

from app.auth import get_current_user_with_ws
from app.realtime.connection_manager import ConnectionManager

router = APIRouter(prefix="/ws", tags=["websocket"])
connection_manager = ConnectionManager()

@router.websocket("/{user_id}")
async def websocket_endpoint(user_id: str, websocket: WebSocket, current_user = Depends(get_current_user_with_ws)):
    """
    **Adds the logged in user to the list of currently connected users and allows them to receive real-time notifications.**

    Parameters:
    *   **user_id** (str): the identifier forof the user attempting to connect. must match the logged-in user's identifier.
    *   **websocket** (Websocket): the WebSocket connection for the user
    *   **current_user** (User): the authenticated user. automatically passed as argument.
    
    Returns: None

    Raises:
    *   **WebSocketException** (code = WS_1008_POLICY_VIOLATION): if the Authorization header is missing from the WebSocket request
    *   **HTTPException** (status_code = 401): if user's token is invalid or expired
    *   **HTTPException** (status_code = 403): if current user's id does not match user id in url
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You are not authorized to connect this user")
    await connection_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id, websocket)
        