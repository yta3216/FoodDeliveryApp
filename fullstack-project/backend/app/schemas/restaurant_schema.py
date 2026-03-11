"""
This module defines the basic restaurant schema for the application.
This includes the menu details as well.

Any updates to the restaurant details should follow this schema.
"""
import re
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
    tags: list[str] = Field(default_factory=list)  # Optional tags for the menu item (spicy, vegetarian, etc.)

# Menu object which contains a list of menu items.
class Menu(BaseModel):
    items: list[MenuItem] = []

# Menu Item Create model for input validation when creating a new menu item.
class MenuItem_Create(BaseModel):
    name: str
    price: float
    tags: list[str] = Field(default_factory=list)

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
        if v < 0:
            raise ValueError("Menu item price must be greater or equal to 0")
        if v > 1000:
            raise ValueError("Menu item price cannot exceed 1000")
        return round(v,2)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
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
    tags: list[str] = Field(default_factory=list)

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
        if v < 0:
            raise ValueError("Menu item price must be greater than 0")
        if v > 1000:
            raise ValueError("Menu item price cannot exceed 1000")
        return round(v,2)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
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
    items: list[MenuItem_Create] = Field(default_factory=list)  # list of menu items to add to restaurant's menu.

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v

# Menu Bulk Update model for input validation when updating multiple menu items in a restaurant's menu.
class MenuItem_Bulk_Update(BaseModel):
    items: list[MenuItem_Update] = Field(default_factory=list)  # list of menu items to update in restaurant's menu.

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v
    
# Menu Create model for when a restaurant menu is initially created.
class Menu_Create(BaseModel):
    items: list[MenuItem_Create] = []

# Restaurant model
# Each restaurant is associated with a single menu
class Restaurant(BaseModel):
    id: int
    name: str
    city: str
    address: Address
    manager_ids: list[str]  # list of user IDs who are managers of the restaurant
    max_delivery_radius_km: float = 10.0  # default delivery radius in km
    menu: Menu = Menu()

# Restaurant Create model for input validation when creating a new restaurant.
# This does not include the 'id' field since it is generated by the system.
# It also does not include the 'menu' field since it is created when the restaurant is created.
# It also does not include the 'manager_ids' field since the only manager on creation is the logged in user.
class Restaurant_Create(BaseModel):
    name: str
    city: str
    address: Address
    max_delivery_radius_km: float = 10.0  # how far the restaurant will deliver
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

# Restaurant Search model to search for restaurants by name, address, or menu item.
# Address fields are stored separately to allow for more specific searching and filtering.
class Restaurant_Search(BaseModel):
    name: str | None = None
    city: str | None = None
    street: str | None = None
    province: str | None = None
    postal_code: str | None = None
    menu_item: str | None = None
    sort_price: str | None = None
    page: int = 1       # which page to return, starts at 1
    page_size: int = 5  # how many results per page

    @field_validator("sort_price")
    @classmethod
    def validate_sort_price(cls,v:str | None) -> str | None:
        if v is not None and v not in ("asc","desc"):
            raise ValueError("sort_price must be either 'asc' or 'desc'")
        return v

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page must be 1 or greater")
        return v

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("page_size must be between 1 and 50")
        return v

# paginated response wrapper so the frontend knows the total results and page info
class PaginatedRestaurantResults(BaseModel):
    results: list[Restaurant]
    total: int        # total number of matching restaurants
    page: int         # current page
    page_size: int    # results per page
    total_pages: int  # total number of pages

# Restaurant Details Update model for input validation when updating restaurant details.
class Restaurant_Details_Update(BaseModel):
    id: int
    name: str
    city: str
    address: Address
    max_delivery_radius_km: float = 10.0  # how far the restaurant will deliver

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
    manager_ids: list[str]

    @field_validator("manager_ids")
    @classmethod
    def validate_manager_ids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one manager is required")
        sanitized = []
        for mid in v:
            mid = mid.strip()
            if not mid:
                raise ValueError("Manager ID cannot be empty")
            sanitized.append(mid)
        return sanitized

