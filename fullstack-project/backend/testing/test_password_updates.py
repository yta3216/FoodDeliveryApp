"""Test cases for password reset and update flows."""

from fastapi import FastAPI
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.repositories.user_repo import load_users, save_users
from app.services.config_service import get_reset_token_expiry_default

client = TestClient(app)

# generic test user's email
test_email = "testingtesting123@example.com"
test_password = "testpassword"

# create a generic user to use in tests. returns login token and user id
@pytest.fixture
def register_user():
    client.post("/user", json={
        "email": test_email,
        "password": test_password,
        "name": "Password Testing",
        "age": 56,
        "gender": "female",
        "role": "customer"
    })
    response = client.post("/user/login", json={"email": test_email, "password": test_password})
    return response.json()

# send a successful password reset request
def test_password_reset_request(register_user):
    email = register_user.get("email")
    response = client.post("/user/password-reset/request", json={"email": email})
    assert response.status_code == 200
    assert response.json().get("detail") == "If the email exists, a password reset link has been sent."

# test password reset with valid token
def test_password_reset(register_user):
    user_id = register_user.get("user_id")
    email = register_user.get("email")
    client.post("/user/password-reset/request", json={"email": email})
    reset_token = get_user_reset_token(user_id)
    new_password = "newpassword"

    response = client.patch("/user/password-reset", json={"new_password": new_password, "reset_token": reset_token})
    assert response.status_code == 200
    
    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            new_password_response = user.get("password")
            break
    assert new_password_response == new_password

# check that expired reset token is rejected
def test_password_reset_expired_token(register_user):
    user_id = register_user.get("user_id")
    email = register_user.get("email")
    client.post("/user/password-reset/request", json={"email": email})
    reset_token = get_user_reset_token(user_id)
    new_password = "newpassword"

    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            user["reset_token_expiry"] -= (get_reset_token_expiry_default() + 20)
            break
    save_users(users)

    response = client.patch("/user/password-reset", json={"new_password": new_password, "reset_token": reset_token})
    assert response.status_code == 400
    assert response.json().get("detail") == "Reset token has expired"

# helper for password reset tests to get the user's reset token
def get_user_reset_token(user_id):
    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            return user.get("reset_token")

# test password reset with invalid token
def test_password_reset_wrong_token():
    response = client.patch("/user/password-reset", json={"new_password": "newpassword", "reset_token": "invalidtoken"})
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid reset token"

# test successful logged-in user password change
def test_password_update(register_user):
    user_id = register_user.get("user_id")
    auth_token = register_user.get("token") 
    user_email = register_user.get("email")
    old_password = test_password
    new_password = "updatedpassword"
    response = client.patch(f"/user/{user_id}/password", json={
        "email": user_email,
        "old_password": old_password,
        "new_password": new_password
        }, headers={"Authorization": f"Bearer {auth_token}"})
    print(response.json())

    assert response.status_code == 200

    users = load_users()
    for user in users:
        if user.get("id") == user_id:
            new_password_response = user.get("password")
            break
    assert new_password_response == new_password

# test logged-in user password change with wrong password
def test_password_update_wrong_pw(register_user):
    user_id = register_user.get("user_id")
    auth_token = register_user.get("token") 
    user_email = register_user.get("email")
    old_password = "wrongpassword"
    new_password = "updatedpassword"
    response = client.patch(f"/user/{user_id}/password", json={
        "email": user_email,
        "old_password": old_password,
        "new_password": new_password
        }, headers={"Authorization": f"Bearer {auth_token}"})
    print(response.json())

    assert response.status_code == 400
    assert response.json().get("detail") == "Old password is incorrect"