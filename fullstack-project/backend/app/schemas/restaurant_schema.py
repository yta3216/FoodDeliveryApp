"""
This module defines the basic restaurant schema for the application.
This includes the menu details as well.

Any updates to the restaurant details should follow this schema.
"""
import re
from typing import List
from pydantic import BaseModel, Field, field_validator

#Address model for validating address input when creating or updating restaurant details.
# Helpers for address input contraints
_NAME_RE = re.compile(r"^[\w\s\-',\.&]+$",re.UNICODE)  # Allows letters, numbers, spaces, and common punctuation
_STREET_RE = re.compile(r"^\d+\s+\S+",re.UNICODE)  # Allows letters, numbers, spaces, and common punctuation
_POSTAL_CODE_RE = re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$") # Canadian postal code format

PROVINCES = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}

class Address(BaseModel):
    street: str
    city: str
    province: str
    postal_code: str

    @field_validator("street")
    @classmethod
    def validate_street(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Street address cannot be empty")
        if len(v)> 100:
            raise ValueError("Street address cannot be longer than 100 characters")
        if not _STREET_RE.match(v):
            raise ValueError("Street address must start with a number followed by the street name (e.g. '123 Main St')")
        return v
    
    @field_validator("city")
    @classmethod
    def validate_city(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("City cannot be empty")
        if len(v)>100:
            raise ValueError("City cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("City contains invalid characters")
        return v
    
    @field_validator("province")
    @classmethod
    def validate_province(cls,v:str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Province cannot be empty")
        if v not in PROVINCES:
            raise ValueError(f"Province must be one of {PROVINCES}")
        return v

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls,v:str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Postal code cannot be empty")
        if not _POSTAL_CODE_RE.match(v):
            raise ValueError("Postal code must be in the format 'A1A 1A1'")
        if len(v) == 6:
            v = v[:3]+ " " + v[3:]
        return v
    
# Menu item model
class MenuItem(BaseModel):
    id: int
    name: str
    price: float
    tags: List[str] = Field(default_factory=list)  # Optional tags for the menu item (spicy, vegetarian, etc.)

# Menu object which contains a list of menu items.
class Menu(BaseModel):
    items: List[MenuItem] = []

# Menu Item Create model for input validation when creating a new menu item.
class MenuItem_Create(BaseModel):
    name: str
    price: float
    tags: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Menu item name cannot be empty")
        if len(v) > 100:
            raise ValueError("Menu item name cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Menu item name contains invalid characters")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls,v:float) -> float:
        if v <= 0:
            raise ValueError("Menu item price must be greater than 0")
        if v > 1000:
            raise ValueError("Menu item price cannot exceed 1000")
        return round(v,2)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        cleaned: List[str] = []
        for v in tags:
            v = v.strip()
            if not v:
                raise ValueError("Tag cannot be empty")
            if len(v) > 50:
                raise ValueError("Tag cannot be longer than 50 characters")
            cleaned.append(v.lower())
        return cleaned

# Menu Item Update model for input validation when updating menu item details.
class MenuItem_Update(BaseModel):
    id: int
    name: str
    price: float
    tags: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Menu item name cannot be empty")
        if len(v) > 100:
            raise ValueError("Menu item name cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Menu item name contains invalid characters")
        return v
    
    @field_validator("price")
    @classmethod
    def validate_price(cls,v:float) -> float:
        if v <= 0:
            raise ValueError("Menu item price must be greater than 0")
        if v > 1000:
            raise ValueError("Menu item price cannot exceed 1000")
        return round(v,2)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        cleaned: List[str] = []
        for v in tags:
            v = v.strip()
            if not v:
                raise ValueError("Tag cannot be empty")
            if len(v) > 50:
                raise ValueError("Tag cannot be longer than 50 characters")
            cleaned.append(v.lower())
        return cleaned
    
# Menu Bulk Create model for input validation when adding multiple menu items to a restaurant's menu.
class MenuItem_Bulk_Create(BaseModel):
    items: List[MenuItem_Create] = Field(default_factory=list)  # List of menu items to add to restaurant's menu.

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v

# Menu Bulk Update model for input validation when updating multiple menu items in a restaurant's menu.
class MenuItem_Bulk_Update(BaseModel):
    items: List[MenuItem_Update] = Field(default_factory=list)  # List of menu items to update in restaurant's menu.

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v
    
# Menu Create model for when a restaurant menu is initially created.
class Menu_Create(BaseModel):
    items: List[MenuItem_Create] = []

# Restaurant model
# Each restaurant is associated with a single menu
class Restaurant(BaseModel):
    id: int
    name: str
    city: str
    address: Address
    manager_ids: List[str]  # List of user IDs who are managers of the restaurant
    menu: Menu = Menu()

# Restaurant Create model for input validation when creating a new restaurant.
# This does not include the 'id' field since it is generated by the system.
# It also does not include the 'menu' field since it is created when the restaurant is created.
# It also does not include the 'manager_ids' field since the only manager on creation is the logged in user.
class Restaurant_Create(BaseModel):
    name: str
    city: str
    address: Address
    menu: Menu_Create = Menu_Create()  # Optional Menu when creating a restaurant

    @field_validator("name")
    @classmethod
    def validate_name(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Restaurant name cannot be empty")
        if len(v) > 100:
            raise ValueError("Restaurant name cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Restaurant name contains invalid characters")
        return v
    
    @field_validator("city")
    @classmethod
    def validate_city(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Restaurant city cannot be empty")
        if len(v) > 100:
            raise ValueError("Restaurant city cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Restaurant city contains invalid characters")
        return v

# Restaurant Details Update model for input validation when updating restaurant details.
class Restaurant_Details_Update(BaseModel):
    id: int
    name: str
    city: str
    address: Address

    @field_validator("name")
    @classmethod
    def validate_name(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Restaurant name cannot be empty")
        if len(v) > 100:
            raise ValueError("Restaurant name cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Restaurant name contains invalid characters")
        return v
    
    @field_validator("city")
    @classmethod
    def validate_city(cls,v:str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Restaurant city cannot be empty")
        if len(v) > 100:
            raise ValueError("Restaurant city cannot be longer than 100 characters")
        if not _NAME_RE.match(v):
            raise ValueError("Restaurant city contains invalid characters")
        return v
    
# Restaurant Managers Update model for input validation when updating restaurant managers.
class Restaurant_Managers_Update(BaseModel):
    id: int
    manager_ids: List[str]

    @field_validator("manager_ids")
    @classmethod
    def validate_manager_ids(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one manager is required")
        sanitized = []
        for mid in v:
            mid = mid.strip()
            if not mid:
                raise ValueError("Manager ID cannot be empty")
            sanitized.append(mid)
        return sanitized

