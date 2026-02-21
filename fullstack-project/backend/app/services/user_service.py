import uuid
from typing import List
from fastapi import HTTPException
from app.repositories.user_repo import load_users, save_users
from app.schemas.user_schema import user


def create_user(payload: user) -> user:
    users = load_users()
    new_id = str(uuid.uuid4()) # generate unique ID for the new user
    if any(user.get("id") == new_id for user in users):
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    new_user = {
        "id": new_id,
        "email": payload.email.strip(),
        "password": payload.password.strip()
    }
    users.append(new_user)
    save_users(users)
    return new_user

