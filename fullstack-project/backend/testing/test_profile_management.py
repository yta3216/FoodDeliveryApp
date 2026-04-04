"""Test cases for user profile management, viewing, and updating profile details."""

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.services.user_service import withdraw_from_wallet, deposit_to_wallet, get_user_by_id

client = TestClient(app)

# helper to register a user and log in, returns the auth token and user id
def register_and_login(email, password="Password123", role="customer"):
    signup_response = client.post("/user", json={
        "email": email,
        "password": password,
        "name": "Test User",
        "age": 25,
        "gender": "male",
        "role": role
    })
    response = client.post("/user/login", json={"email": email, "password": password})
    data = response.json()
    return data.get("token"), data.get("user_id")

# ------------ viewing profile ----------------- #

def test_user_can_view_own_profile():
    token, user_id = register_and_login("viewprofile@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("email") == "viewprofile@example.com"
    assert data.get("age") == 25
    assert data.get("gender") == "male"
    assert data.get("role") == "customer"

def test_password_not_returned_in_profile():
    token, user_id = register_and_login("nopwdprofile@example.com")
    response = client.get(f"/user/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    # password should never be returned
    assert "password" not in response.json()

# -------------- updating profile -------------- #

def test_user_can_update_own_details():
    token, user_id = register_and_login("updateme@example.com")
    response = client.put(f"/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "updated@example.com",
            "name": "Updated Name",
            "age": 30,
            "gender": "other",
            "role": "customer"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("email") == "updated@example.com"
    assert data.get("name") == "Updated Name"
    assert data.get("age") == 30
    assert data.get("gender") == "other"

def test_role_cannot_be_changed_by_user():
    token, user_id = register_and_login("rolechange@example.com")
    response = client.put(f"/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "rolechange@example.com",
            "name": "Test User",
            "age": 25,
            "gender": "male",
            "role": "admin"  # trying to upgrade to admin
        }
    )
    # role should stay as customer regardless
    assert response.status_code == 200
    assert response.json().get("role") == "customer"

def test_update_requires_authentication():
    _, user_id = register_and_login("noauthupdate@example.com")
    response = client.put(f"/user/{user_id}",
        json={
            "email": "hacked@example.com",
            "name": "Hacker",
            "age": 30,
            "gender": "male",
            "role": "customer"
        }
    )
    assert response.status_code == 401  # missing authorization header


# ---------- Updating wallet balance ------------- #

# test depositing to an empty wallet (newly created)
def test_deposit_to_empty_wallet():
    token, user_id = register_and_login("deposit1@example.com")
    customer = get_user_by_id(user_id)
    deposit_amount = 5.45
    wallet_balance = deposit_to_wallet(deposit_amount, customer)
    assert wallet_balance == deposit_amount
    
# test depositing multiple times
def test_multi_deposit():
    token, user_id = register_and_login("deposit2@example.com")
    customer = get_user_by_id(user_id)
    first_deposit_amount = 10.5
    wallet_balance = deposit_to_wallet(first_deposit_amount, customer)
    assert wallet_balance == first_deposit_amount

    second_deposit_amount = 7.35
    wallet_balance = deposit_to_wallet(second_deposit_amount, customer)
    assert wallet_balance == first_deposit_amount + second_deposit_amount

# test depositing but amount is negative
def test_invalid_deposit():
    token, user_id = register_and_login("deposit3@example.com")
    customer = get_user_by_id(user_id)
    deposit_amount = -1.55
    with pytest.raises(HTTPException) as e:
        deposit_to_wallet(deposit_amount, customer)
    assert e.value.status_code == 400

# test multiple successful withdraws sequentially
def test_multi_withdraw():
    token, user_id = register_and_login("withdraw1@example.com")
    customer = get_user_by_id(user_id)
    deposit_amount = 100
    withdraw_amount = 20
    initial_balance = deposit_to_wallet(deposit_amount, customer)
    single_withdraw_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert single_withdraw_balance == initial_balance - withdraw_amount

    second_withdraw_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert second_withdraw_balance == initial_balance - 2*withdraw_amount

# test withdrawing from empty wallet (newly created)
def test_withdraw_from_empty_wallet():
    token, user_id = register_and_login("withdraw2@example.com")
    customer = get_user_by_id(user_id)
    withdraw_amount = 5.00
    with pytest.raises(HTTPException) as e:
        wallet_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert e.value.status_code == 400
    assert e.value.detail == "Customer does not have sufficient wallet funds."

# test withdrawing a negative amount
def test_withdraw_negative_amount():
    token, user_id = register_and_login("withdraw3@example.com")
    customer = get_user_by_id(user_id)
    withdraw_amount = -5.00
    with pytest.raises(HTTPException) as e:
        wallet_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert e.value.status_code == 400
    assert e.value.detail == "A negative amount cannot be withdrawn from wallet"

# test withdrawing once successfully then balance is too low to withdraw again
def test_second_withdraw_unsuccessful():
    token, user_id = register_and_login("withdraw4@example.com")
    customer = get_user_by_id(user_id)
    deposit_amount = 30
    withdraw_amount = 20
    initial_balance = deposit_to_wallet(deposit_amount, customer)
    single_withdraw_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert single_withdraw_balance == initial_balance - withdraw_amount
    
    with pytest.raises(HTTPException) as e:
        wallet_balance = withdraw_from_wallet(withdraw_amount, customer)
    assert e.value.status_code == 400
    assert e.value.detail == "Customer does not have sufficient wallet funds."