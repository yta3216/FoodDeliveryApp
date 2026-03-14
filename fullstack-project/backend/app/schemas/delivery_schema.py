from pydantic import BaseModel

# a single delivery person
class Driver(BaseModel):
    id: int
    status: str = "available"   # available or unavailable
    ready_at: float = 0.0       # unix timestamp of when they'll be available again

# the delivery itself, linked to an order
class Delivery(BaseModel):
    id: int
    order_id: int
    driver_id: int
    method: str                 # bike or car
    distance_km: float
    eta_minutes: float
    started_at: float = 0.0     # unix timestamp when status hit delivering
    delivered_at: float = 0.0   # unix timestamp when status hit delivered
    actual_minutes: float = 0.0 # calculated when delivered