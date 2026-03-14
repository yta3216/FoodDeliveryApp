from pydantic import BaseModel

# the delivery record, linked to an order and a driver
class Delivery(BaseModel):
    id: int
    order_id: int
    driver_id: str          # matches the user id of the delivery driver
    method: str             # bike or car
    distance_km: float
    eta_minutes: float = 0.0        # calculated when status hits delivering
    started_at: float = 0.0         # unix timestamp when driver marks delivering
    delivered_at: float = 0.0       # unix timestamp when driver marks delivered
    actual_minutes: float = 0.0     # calculated when delivered
    delay_minutes: float = 0.0      # actual_minutes - eta_minutes, negative = early, positive = late