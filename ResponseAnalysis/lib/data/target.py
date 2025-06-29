# @author: Sudarsun
# @date: 2025-06-28
#
# This module defines the Target class, which represents a target in the AI evaluation system.

from pydantic import BaseModel, Field
from typing import Any, Optional

class Target(BaseModel):
    """
    Represents a target in the response analysis system.
    Attributes:
        name (str): The name of the target.
        description (str): A brief description of the target.
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    target_name: str = Field(..., description="The name of the target.")
    target_type: str = Field(default="WhatsApp", description="The type of the target, e.g., 'WhatsApp', 'WebApp', 'API', etc.")
    target_description: str = Field(..., description="A brief description of the target.")
    target_url: str = Field(..., description="The URL of the target (if applicable).")
    target_domain: str = Field(default="general", description="The domain name to which the target belongs.")
    target_languages: list[str] = Field(..., description="List of languages supported by the target.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, target_name: str, target_type: str, target_url: str, target_languages: list[str], target_description: Optional[str] = None,  target_domain: str = "general", **kwargs):
        """
        Initializes a Target instance.
        Args:
            target_name (str): The name of the target.
            target_type (str): The type of the target.
            target_description (str): A brief description of the target.
            target_url (str): The URL of the target (if applicable).
            target_domain (str): The domain name to which the target belongs.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(target_name=target_name, target_type=target_type, target_description=target_description, target_url=target_url, target_domain=target_domain, target_languages=target_languages, kwargs=kwargs)

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
        return f"Target(name='{self.target_name}', type='{self.target_type}', url='{self.target_url}')"
    
    def __str__(self):
        return f"Target name: '{self.target_name}'\tTarget type: '{self.target_type}'\tTarget URL: '{self.target_url}'\tTarget description: '{self.target_description}'"
    
    def __eq__(self, other):
        """
        Checks equality between two Target instances.
        Compares both name and description.
        """
        if isinstance(other, Target):
            return (self.target_name == other.target_name and 
                    self.target_type == other.target_type and 
                    self.target_description == other.target_description and
                    self.target_url == other.target_url)
        return False    
    
    def __hash__(self):
        """
        Returns a hash of the Target instance.
        This allows Target instances to be used as keys in dictionaries or added to sets.
        """
        return hash((self.target_name, self.target_type, self.target_description, self.target_url))
    
