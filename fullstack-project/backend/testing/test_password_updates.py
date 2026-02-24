"""testing password updates workflows"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# create a user to test with
client.post("/user", json={"email": "testing123@example.com", "password": "passwordpassword"})

def test_password_reset_request():
    response = client.post("/user/password-reset/request", json={"email": "testing123@example.com"})
    assert response.status_code == 200
    assert response.json().get("detail") == "If the email exists, a password reset link has been sent."

# TODO: check a successful password reset flow, 
# but this is difficult to test since the reset token 
# is printed to the console and not returned in the response.

def test_password_reset():
    response = client.post("/user/reset-password", json={"new_password": "newpassword", "reset_token": "invalidtoken"})
    assert response.status_code == 400
    assert response.json().get("detail") == "Invalid reset token"

# TODO: check that expired reset token is rejected

# TODO: check that logged in user can update password with 
# correct old password, and cannot with incorrect old password.