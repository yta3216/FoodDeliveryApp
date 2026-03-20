"""
This module defines the basic restaurant schema for the application.
This includes the menu details as well.

Any updates to the restaurant details should follow this schema.
"""
import re
from pydantic import BaseModel, Field, field_validator

# Helpers for address input contraints
_NAME_RE = re.compile(r"^[\w\s\-',\.&]+$",re.UNICODE)  # Allows letters, numbers, spaces, and common punctuation
_STREET_RE = re.compile(r"^\d+\s+\S+",re.UNICODE)  # Allows letters, numbers, spaces, and common punctuation
_POSTAL_CODE_RE = re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$") # Canadian postal code format

PROVINCES = {"AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT"}

class Address(BaseModel):
    """
    **Defines the attributes of an address.**

    Attributes:
    *   **street** (str): restaurant's street address. must start with number followed by street name
    *   **city** (str): restaurant's city
    *   **province** (str): restaurant's province, written as a 2 letter abbreviation
    *   **postal_code** (str): restaurant's postal code. must follow the format A1A 1A1
    """
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
    
class MenuItem(BaseModel):
    """
    **Defines the attributes of a generic menu item.**

    Attributes:
    *   **id** (int): the identifier of the menu item
    *   **name** (str): the name of the menu item
    *   **price** (float): the price of the menu item
    *   **tags** list[str]: tags for the item (spicy, vegetarian, etc.) *(optional)*
    """
    id: int
    name: str
    price: float
    tags: list[str] = Field(default_factory=list)

class Menu(BaseModel):
    """
    **Defines the attributes of a menu object.**

    Attributes:
    *   **items** (list[MenuItem]): a list of the items in this menu
    """
    items: list[MenuItem] = []

class MenuItem_Create(BaseModel):
    """
    **Defines the attributes required to create a menu item.**

    Attributes:
    *   **name** (str): the name of the new menu item
    *   **price** (float): the price of the new menu item
    *   **tags** list[str]: tags for the item (spicy, vegetarian, etc.) *(optional)*
    """
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

class MenuItem_Update(BaseModel):
    """
    **Defines the attributes required to update a menu item.**
    
    Attributes:
    *   **id** (int): the identifier of the menu item to be updated
    *   **name** (str): the name of the updated menu item
    *   **price** (float): the price of the updated menu item
    *   **tags** list[str]: updated tags for the item (spicy, vegetarian, etc.) *(optional)*
    """
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
    
class MenuItem_Bulk_Create(BaseModel):
    """
    **Defines the attributes required to add several items to a restaurant menu at once.**

    Attributes:
    *   **items** (list[MenuItem_Create]): list of new menu items to add to restaurant's menu
    """
    items: list[MenuItem_Create] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v

class MenuItem_Bulk_Update(BaseModel):
    """
    **Defines the attributes required to modify several items to a restaurant menu at once.**

    Attributes:
    *   **items** (list[MenuItem_Create]): list of existing menu items to update
    """
    items: list[MenuItem_Update] = Field(default_factory=list)

    @field_validator("items")
    @classmethod
    def validate_items(cls,v:list) -> list:
        if not v:
            raise ValueError("At least one menu item must be provided")
        return v
    
class Menu_Create(BaseModel):
    """
    **Defines the attributes required to create a menu for a restaurant.**

    Attributes:
    *   **items** (list[MenuItem_Create]): list of menu items that will comprise the restaurant's new menu
    """
    items: list[MenuItem_Create] = []

class Restaurant(BaseModel):
    """
    **Defines the attributes of a generic restaurant model.
    Restaurants are associated with one menu.**

    Attributes:
    *   **id** (int): the restaurant's identifier
    *   **name** (name): the restaurant's name
    *   **city** (str): the city the restaurant is located in
    *   **address** (Address): the full address of the restaurant
    *   **manager_ids** (list[str]): list of user IDs who are managers of the restaurant
    *   **max_delivery_radius_km** (float): the maximum radius that a restaurant will deliver to. *(optional; default = 10)*
    *   **delivery_fee** (float): the fee charged for delivery by this restaurant. *(optional; default = 0)*
    *   **menu** (Menu): the restaurant's menu
    """
    id: int
    name: str
    city: str
    address: Address
    manager_ids: list[str]
    max_delivery_radius_km: float = 10.0
    delivery_fee: float = 0.0
    menu: Menu = Menu()

class Restaurant_Create(BaseModel):
    """
    **Defines the attributes required to create a restaurant. Initial manager id is just the current user.**

    Attributes:
    *   **name** (name): the restaurant's name
    *   **city** (str): the city the restaurant is located in
    *   **address** (Address): the full address of the restaurant
    *   **max_delivery_radius_km** (float): the maximum radius that a restaurant will deliver to. *(optional; default = 10)*
    *   **delivery_fee** (float): the fee charged for delivery by this restaurant. *(optional; default = 0)*
    *   **menu** (Menu): the restaurant's menu, empty if not provided *(optional; default = empty menu)*
    """
    name: str
    city: str
    address: Address
    max_delivery_radius_km: float = 10.0
    delivery_fee: float = 0.0
    menu: Menu_Create = Menu_Create()

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
    
    @field_validator("delivery_fee")
    @classmethod
    def round_delivery_fee(cls, v:float) -> float:
        return round(v, 2)

class Restaurant_Search(BaseModel):
    """
    **Defines the available search criteria. All attributes are optional.**

    Attributes:
    *   **name** (str)
    *   **city** (str)
    *   **street** (str)
    *   **province** (str)
    *   **postal_code** (str)
    *   **menu_item** (str): name of a menu item
    *   **sort_price** (str): "asc" (sorts ascending) or "desc" (sorts descending)
    *   **page** (str): which page to return from paginated results. starts at 1
    *   **name** (str): how many results should be returned per page (1-50)
    """
    name: str | None = None
    city: str | None = None
    street: str | None = None
    province: str | None = None
    postal_code: str | None = None
    menu_item: str | None = None
    sort_price: str | None = None
    page: int = 1
    page_size: int = 5

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

class PaginatedRestaurantResults(BaseModel):
    """
    **Defines the attributes of search pagination for the frontend.**

    Attributes:
    *   **results** (list[Restaurant]): list of matching restaurants
    *   **total** (int): total number of matching restaurants
    *   **page** (int): current page number
    *   **page_size** (int): number of results returned per page
    *   **total_pages** (int): total number of pages returned
    """
    results: list[Restaurant]
    total: int
    page: int
    page_size: int
    total_pages: int

class Restaurant_Details_Update(BaseModel):
    """
    **Defines the attributes required to update restaurant details.**

    Attributes:
    *   **id** (int): identifier of restaurant to be updated
    *   **name** (str): updated restaurant name
    *   **city** (str): updated restaurant city
    *   **address** (Address): updated restaurant address
    *   **max_delivery_radius_km** (float): maximum distance that the restaurant will accept orders from. *(optional; default = 10)*
    *   **delivery_fee** (float): the fee charged for delivery by this restaurant. *(optional; default = 0)*
    """
    id: int
    name: str
    city: str
    address: Address
    max_delivery_radius_km: float = 10.0
    delivery_fee: float = 0.0

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
    
    @field_validator("delivery_fee")
    @classmethod
    def round_delivery_fee(cls, v:float) -> float:
        return round(v, 2)
    
class Restaurant_Managers_Update(BaseModel):
    """
    **Defines the attributes required to update the list of restaurant managers.**

    Attributes:
    *   **id** (int): the identifier of the restaurant whose managers will be updated
    *   **manager_ids** (list[str]): new list of manager ids for this restaurant
    """
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

