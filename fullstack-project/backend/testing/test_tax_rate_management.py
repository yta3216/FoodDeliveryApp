from fastapi.testclient import TestClient
import pytest
from app.main import app
from testing.test_authorization import register_and_login
from testing.test_cart_management import customer_with_token, manager_with_token

client = TestClient(app)

# helper to register an admin user and log in, returns the auth token
@pytest.fixture
def admin_token():
    register_and_login("admin@example.com", role="admin")
    response = client.post("/user/login", json={"email": "admin@example.com", "password": "Password123"})
    return response.json().get("token")

#----------- test updating tax rate --------------#
def test_admin_can_update_tax_rate(admin_token):
    response = client.patch("/config/tax-rate?new_tax_rate=0.67", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == 0.67

def test_customer_cannot_update_tax_rate(customer_with_token):
    response = client.patch("/config/tax-rate?new_tax_rate=0.67", headers={"Authorization": f"Bearer {customer_with_token['token']}"})
    assert response.status_code == 403

def test_manager_cannot_update_tax_rate(manager_with_token):
    response = client.patch("/config/tax-rate?new_tax_rate=0.67", headers={"Authorization": f"Bearer {manager_with_token['token']}"})
    assert response.status_code == 403

#----------- test tax rate input validation --------------#
def test_invalid_tax_rate_rejected(admin_token):
    response = client.patch("/config/tax-rate?new_tax_rate=67676767.67", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 400

def test_negative_tax_rate_rejected(admin_token):
    response = client.patch("/config/tax-rate?new_tax_rate=-0.67", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 400

def test_tax_rate_update_inclusive_one(admin_token):
    response = client.patch("/config/tax-rate?new_tax_rate=1.0", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == 1.0

def test_tax_rate_update_inclusive_zero(admin_token):
    response = client.patch("/config/tax-rate?new_tax_rate=0.0", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == 0.0
