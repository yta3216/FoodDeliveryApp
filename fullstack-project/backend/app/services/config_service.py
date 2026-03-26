""" This module implements business logic for config management. """

from fastapi import HTTPException
from app.repositories.config_repo import load_config, save_config

def get_tax_rate() -> float:
    """
    **Retrieves the current tax rate from the stored configs.**

    Parameters: None

    Returns:
        **float**: the current tax rate, default: 0.12
    """
    return load_config().get("GLOBAL_TAX_RATE", 0.12)

def set_tax_rate(new_tax_rate: float) -> float:
    """
    **Sets the tax rate for the app.**

    Parameters:
        **new_tax_rate** (float): the new tax rate, must be between 0 and 1

    Returns:
        **float**: the new tax rate

    Raises:
        HTTPException (status_code = 400): if the new tax rate is not between 0 and 1
    """
    if not (0 <= new_tax_rate <= 1):
        raise HTTPException(status_code=400, detail="Tax rate must be between 0 and 1")
    
    config = load_config()
    config["GLOBAL_TAX_RATE"] = new_tax_rate
    save_config(config)
    
    return new_tax_rate

def get_bike_speed_default() -> float:
    return load_config().get("BIKE_SPEED_KMH", 20.0)

def get_car_speed_default() -> float:
    return load_config().get("CAR_SPEED_KMH", 50.0)

def get_bike_max_distance_default() -> float:
    return load_config().get("BIKE_MAX_DISTANCE_KM", 5.0)

def get_reset_token_expiry_default() -> float:
    return load_config().get("RESET_TOKEN_EXPIRY", 900)

def get_session_token_expiry_default() -> float:
    return load_config().get("SESSION_TOKEN_EXPIRY", 86400)