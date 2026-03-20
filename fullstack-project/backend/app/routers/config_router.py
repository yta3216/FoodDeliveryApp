""" This module defines the API routes for config management. """

from fastapi import APIRouter, Depends
from app.auth import require_role, UserRole
from app.schemas.user_schema import Admin
from app.services.config_service import set_tax_rate

router = APIRouter(prefix="/config", tags=["config"])

@router.patch("/tax-rate")
def update_tax_rate_router(new_tax_rate: float, current_user: Admin = Depends(require_role(UserRole.ADMIN))):
    """
    **Allows an admin to update the tax rate.**
    
    Parameters:
    *   **new_tax_rate** (float): the new tax rate, must be between 0 and 1
    
    Returns:
    *   **float**: the new tax rate

    Raises:
    *   **HTTPException** (status_code = 400): if the new tax rate is not between 0 and 1
    """
    return set_tax_rate(new_tax_rate)