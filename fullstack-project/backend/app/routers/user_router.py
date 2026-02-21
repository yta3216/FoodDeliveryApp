from typing import List
from fastapi import APIRouter, status
from app.schemas.user_schema import User, User_Create, User_Update
from app.services.user_service import create_user, get_user_by_id

router = APIRouter(prefix="/user", tags=["user"])


# post request to create a new user
# we use the User_Create schema because we dont want the client to send an id
@router.post("", response_model=User, status_code=201)
def post_user(payload: User_Create):
    return create_user(payload)

# get request to retrieve a user by id
@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    return get_user_by_id(user_id)
