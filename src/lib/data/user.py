# @date: 2025-10-24
#
# This module defines the User class, which represents a user in the AI evaluation system.

from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class User(BaseModel):
    """
    Represents a user in the AI evaluation system.
    Attributes:
        user_name (str): The username of the user.
        role (str): The role of the user (admin, manager, curator, viewer).
        password (str): The hashed password of the user.
        is_active (bool): Whether the user account is active.
        user_id (Optional[str]): The unique identifier for the user (auto-generated).
        created_at (Optional[str]): ISO Timestamp when the user was created.
        updated_at (Optional[str]): ISO Timestamp when the user was last updated.
    """
    user_name: str = Field(..., description="The username of the user.")
    role: str = Field(..., description="The role of the user (admin, manager, curator, viewer).")
    password: str = Field(..., description="The hashed password of the user.")
    is_active: bool = Field(default=True, description="Whether the user account is active.")
    user_id: Optional[str] = Field(None, description="The unique identifier for the user (auto-generated).")
    created_at: Optional[str] = Field(None, description="ISO Timestamp when the user was created.")
    updated_at: Optional[str] = Field(None, description="ISO Timestamp when the user was last updated.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, user_name: str, role: str, password: str, is_active: bool = True, user_id: Optional[str] = None, created_at: Optional[str] = None, updated_at: Optional[str] = None, **kwargs):
        """
        Initializes a User instance.
        Args:
            user_name (str): The username of the user.
            role (str): The role of the user (admin, manager, curator, viewer).
            password (str): The hashed password of the user.
            is_active (bool): Whether the user account is active.
            user_id (Optional[str]): The unique identifier for the user (auto-generated).
            created_at (Optional[str]): ISO Timestamp when the user was created.
            updated_at (Optional[str]): ISO Timestamp when the user was last updated.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(user_name=user_name, role=role, password=password, is_active=is_active, user_id=user_id, created_at=created_at, updated_at=updated_at, kwargs=kwargs)

    def __getattr__(self, name: str) -> Any:
        """
        Allows access to additional keyword arguments as attributes.
        If the attribute does not exist, raises an AttributeError.
        Args:
            name (str): The name of the attribute to access.
        Returns:
            Any: The value of the attribute if it exists in kwargs.
        Raises:
            AttributeError: If the attribute does not exist in kwargs.
        """
        if name.startswith('_') or name not in self.kwargs:
            # Prevent access to private attributes
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self.kwargs.get(name)
    
    def __repr__(self):
        """
        Returns a string representation of the User instance for debugging.
        """
        return f"User(user_id='{self.user_id}', user_name='{self.user_name}', role='{self.role}', is_active={self.is_active})"
    
    def __str__(self):
        """
        Returns a string representation of the user.
        """
        return f"User: '{self.user_name}' (Role: {self.role}, Active: {self.is_active})"
    
    def __eq__(self, other):
        """
        Checks equality between two User instances.
        Compares user_name, role, and is_active.
        """
        if not isinstance(other, User):
            return False
        return (self.user_name == other.user_name and
                self.role == other.role and
                self.is_active == other.is_active)
    
    def __hash__(self):
        """
        Returns a hash of the User instance.
        Uses the hash of user_name, role, and is_active.
        """
        return hash((self.user_name, self.role, self.is_active))


class Login(BaseModel):
    """
    Represents a login attempt in the AI evaluation system.
    Attributes:
        user_name (str): The username of the user attempting to log in.
        password (str): The password provided for the login attempt.
    """
    user_name: str = Field(..., description="The username of the user attempting to log in.")
    password: str = Field(..., description="The password provided for the login attempt.")

    def __init__(self, user_name: str, password: str):
        """
        Initializes a Login instance.
        Args:
            user_name (str): The username of the user attempting to log in.
            password (str): The password provided for the login attempt.
        """
        super().__init__(user_name=user_name, password=password)

    def __repr__(self):
        """
        Returns a string representation of the Login instance for debugging.
        """
        return f"Login(user_name='{self.user_name}')"
    
    def __str__(self):
        """
        Returns a string representation of the login attempt.
        """
        return f"Login Attempt: '{self.user_name}'"