"""
This module defines the basic user schema for the application.

Any updated to the users account details should follow this schema.
"""

from enum import Enum
from pydantic import BaseModel, field_validator, EmailStr

from .cart_schema import Cart

class UserRole(str, Enum):
    """
    **User role enumeration to define a fixed set of roles.**
    
    Attributes:
    *   **CUSTOMER**: "customer"
    *   **RESTAURANT_MANAGER**: "manager"
    *   **ADMIN**: "admin"
    *   **DELIVERY_DRIVER** = "driver"
    """
    CUSTOMER = "customer"
    RESTAURANT_MANAGER = "manager"
    ADMIN = "admin"
    DELIVERY_DRIVER = "driver"

class User(BaseModel):
    """
    **Defines the attributes of a generic user account in the system. All account types share these attributes.**

    Attributes:
    *   **id** (str): user's internal identifier
    *   **email** (str): user's email
    *   **name** (str): user's name
    *   **password** (str): user's password, must be at least 8 characters long
    *   **age** (int): user's age
    *   **gender** (str): client's gender. male, female, other, or prefer not to say
    *   **role** (UserRole): the user's account type, must be one of UserRole enumeration options
    *   **reset_token** (str): password reset token, used when user forgets password and attemps to reset *(optional)*
    *   **reset_token_expiry** (int): token expiry timestamp *(optional)*
    """
    id: str
    email: str
    name: str
    password: str
    age: int
    gender: str
    role: UserRole
    reset_token: str | None = None  # Optional field for password reset token
    reset_token_expiry: int | None = None  # Optional field for token expiry timestamp

class Customer(User):
    """
    **Defines the attributes of a Customer account type, which is for clients who intend to make purchases.
    Includes all generic "User" fields as well as those listed below.**

    Attributes:
    *   **role** (UserRole): always set to UserRole.CUSTOMER
    *   **cart** (Cart): the user's cart, for order creation purposes
    """
    role: UserRole = UserRole.CUSTOMER
    cart: Cart = Cart()

class RestaurantManager(User):
    """
    **Defines the attributes of a RestaurantManager account type, which is for clients who manage restaurants.
    Includes all generic "User" fields as well as those listed below.**

    Attributes:
    *   **role** (UserRole): always set to UserRole.RESTAURANT_MANAGER
    """
    role: UserRole = UserRole.RESTAURANT_MANAGER

class Admin(User):
    """
    **Defines the attributes of an Admin account type, which is for clients who manage the system itself.
    Includes all generic "User" fields as well as those listed below.**

    Attributes:
    *   **role** (UserRole): always set to UserRole.ADMIN
    """
    role: UserRole = UserRole.ADMIN

class DeliveryDriver(User):
    """
    **Defines the attributes of a DeliveryDriver account type, which is for clients who deliver orders to customers.
    Includes all generic "User" fields as well as those listed below.**

    Attributes:
    *   **role** (UserRole): always set to UserRole.DELIVERY_DRIVER
    """
    role: UserRole = UserRole.DELIVERY_DRIVER

# Map user roles to appropriate classes for creation
ROLE_TO_CLASS = {
    UserRole.CUSTOMER: Customer,
    UserRole.RESTAURANT_MANAGER: RestaurantManager,
    UserRole.ADMIN: Admin,
    UserRole.DELIVERY_DRIVER: DeliveryDriver
}

class User_Create(BaseModel):
    """
    **Defines the attribues required to create a user.**

    Attributes:
    *   **email** (EmailStr): user's email
    *   **password** (str): user's password, must be at least 8 characters long
    *   **name** (str): user's name
    *   **age** (int): user's age (0-100)
    *   **gener** (str): users's gender. male, female, other, or prefer not to say
    *   **role** (UserRole): the user's account type, must be one of UserRole enumeration options
    """
    email: EmailStr
    password: str
    name: str
    age: int
    gender: str
    role: UserRole

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v.strip():
            raise ValueError("Email cannot be empty")
        return v.strip()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Age must be between 0 and 100")
        return v
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        allowed = {"male","female","other","prefer not to say"}
        if v.strip().lower() not in allowed:
            raise ValueError("Gender must be one of: male, female, other, prefer not to say");
        return v.strip().lower()

class User_Update(BaseModel):
    """
    **Defines the attributes required to update the user's details. Note that password and role are not changeable here.**

    Attributes:
    *   **email** (EmailStr): the user's updated email
    *   **name** (str): the user's updated name
    *   **age** (int): the user's updated age (0-100)
    *   **gender** (str): the user's updated gender. male, female, other, or prefer not to say
    """
    email: EmailStr
    name: str
    age: int
    gender: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Age must be between 0 and 100")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        allowed = {"male", "female", "other", "prefer not to say"}
        if v.strip().lower() not in allowed:
            raise ValueError("Gender must be one of: male, female, other, prefer not to say")
        return v.strip().lower()

class LoginRequest(BaseModel):
    """
    **Defines the attributes required to log in a user.**

    Attributes:
    *   **email** (str): the user's email
    *   **password** (str): the user's password
    """
    email: str
    password: str

class LoginResponse(BaseModel):
    """
    **Defines the attributes returned when a user successfully logs in.**

    Attributes:
    *   **token** (str): the user's current authentication token
    *   **user_id** (str): the user's identifier
    *   **email** (str): the user's email
    *   **role** (UserRole): the user's account type
    *   **age** (int): the user's age
    *   **gender** (str): the user's gender
    *   **name** (str): the user's name
    """
    token: str
    user_id: str
    email: str
    role: UserRole
    age: int
    gender: str
    name: str

class Password_Reset_Request(BaseModel):
    """
    **Defines the attributes required to request a password reset. Used when user forgets password and needs to reset it.**

    Attributes:
    *   **email** (str): the user's email
    """
    email: str

class Password_Reset(BaseModel):
    """
    **Defines the attributes required to reset the user's password when after have submitted a password reset request.**

    Attributes:
    *   **new_password** (str): the user's new password
    *   **reset_token** (str): the user's reset token, obtained from the password reset request they submitted
    """
    new_password: str
    reset_token: str

class Password_Update_When_Logged_In(BaseModel):
    """
    **Defines the attributes required to update the user's password while they are logged in.**

    Attributes:
    *   **email** (str): the user's email
    *   **old_password** (str): the password currently associated with the user's account
    *   **new_password** (str): the requested new password
    """
    email: str
    old_password: str
    new_password: str

# public-facing user model - excludes password for security
class UserPublic(BaseModel):
    """
    **Defines the attributes returned when user data is requested but password should be hidden for security purposes.**

    Attributes:
    *   **id** (str): user's internal identifier
    *   **email** (str): user's email
    *   **name** (str): user's name
    *   **age** (int): user's age
    *   **gender** (str): user's gender
    *   **role** (UserRole): the user's account type
    """
    id: str
    email: str
    name: str
    age: int
    gender: str
    role: UserRole