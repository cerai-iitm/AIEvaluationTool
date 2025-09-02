# @author: Sudarsun S
# @date: 2025-06-19
# @version: 1.0.0
# @description: This module defines the Strategy class, which represents a strategy with a name and description.

from pydantic import BaseModel, Field
from typing import Any

class Strategy(BaseModel):
    """    Represents a strategy with a name and description.
    This class provides methods for creating a strategy object,
    which represents the approach to evaluating agent responses against the ground truth or description.
    """
    name: str = Field(..., description="The name of the strategy.")
    description: str = Field(..., description="A brief description of the strategy.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, name: str, description: str, **kwargs):
        """ Initializes a Strategy instance.
        Args:
            name (str): The name of the strategy.
            description (str): A brief description of the strategy.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(name=name, description=description, kwargs=kwargs)

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
        return f"Strategy(name='{self.name}', description='{self.description}')"

    def __str__(self):
        return f"Strategy name: '{self.name}'\tStrategy description: '{self.description}'"
    
    def __eq__(self, other):
        """
        Checks equality between two Strategy instances.
        Compares both name and description.
        """
        if isinstance(other, Strategy):
            return self.name == other.name and self.description == other.description
        return False
    
    def __hash__(self):
        """
        Returns a hash of the Strategy instance.
        This allows Strategy instances to be used as keys in dictionaries or added to sets.
        """
        return hash((self.name, self.description))