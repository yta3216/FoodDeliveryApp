"""
This module defines the schema for delivery records.
A delivery record is created when a driver is assigned to an order.
"""
from pydantic import BaseModel


class Delivery(BaseModel):
    """
    **Defines the attributes of a delivery record.**

    Attributes:
    *   **id** (int): the identifier of the delivery record
    *   **order_id** (int): the identifier of the order being delivered
    *   **driver_id** (str): the identifier of the delivery driver assigned to this order
    *   **method** (str): the delivery vehicle type, either *bike* or *car*
    *   **distance_km** (float): the delivery distance in kilometres
    *   **eta_minutes** (float): estimated delivery time in minutes, calculated when the driver starts the delivery
    *   **started_at** (float): unix timestamp of when the driver marked the delivery as started
    *   **delivered_at** (float): unix timestamp of when the driver marked the delivery as completed
    *   **actual_minutes** (float): actual time taken to deliver in minutes
    *   **delay_minutes** (float): difference between actual and estimated time. negative means early, positive means late
    """
    id: int
    order_id: int
    driver_id: str
    method: str
    distance_km: float
    eta_minutes: float = 0.0
    started_at: float = 0.0
    delivered_at: float = 0.0
    actual_minutes: float = 0.0
    delay_minutes: float = 0.0