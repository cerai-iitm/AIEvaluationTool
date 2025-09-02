#@author: Sudarsun
# @date: 2025-06-29
#
# This module defines the Run class, which represents a test run on a specific target application in the AI evaluation system.

from pydantic import BaseModel, Field
from typing import Any, Optional

class Run(BaseModel):
    """
    Represents a test run on a specific target application.
    Attributes:
        target (str): The name of the target application.
        run_name (str): The name of the run, typically a unique identifier.
        start_ts (str): ISO Timestamp when the test run was started.
        end_ts (str): ISO Timestamp when the test run finished (completed/failed).
        status (str): Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.
    """
    target: str = Field(..., description="The name of the target application.")
    run_name: str = Field(..., description="The name of the run, typically a unique identifier.")
    start_ts: str = Field(..., description="ISO Timestamp when the test run was started.")
    end_ts: Optional[str] = Field(None, description="ISO Timestamp when the test run finished (completed/failed).")
    status: str = Field(default='NEW', description="Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility")

    def __init__(self, target: str, run_name: str, start_ts: str, status: str = "NEW", end_ts: Optional[str] = None,**kwargs):
        """
        Initializes a Run instance.
        Args:
            target (str): The name of the target application.
            run_name (str): The name of the run, typically a unique identifier.
            start_ts (str): ISO Timestamp when the test run was started.
            end_ts (str): ISO Timestamp when the test run finished (completed/failed).
            status (str): Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(target=target, run_name=run_name, start_ts=start_ts, end_ts=end_ts, status=status, kwargs=kwargs)

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
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self.kwargs.get(name)
    
    def __repr__(self):
        return f"Run(target='{self.target}', run_name='{self.run_name}', start_ts='{self.start_ts}', end_ts='{self.end_ts}', status='{self.status}')"
    
    def __str__(self):
        return f"Run with target: '{self.target}', run_name: '{self.run_name}', start_ts: '{self.start_ts}', end_ts: '{self.end_ts}', status: '{self.status}'"
    
    def __eq__(self, other):
        if not isinstance(other, Run):
            return NotImplemented
        return (self.target == other.target and
                self.run_name == other.run_name and
                self.start_ts == other.start_ts and
                self.end_ts == other.end_ts and
                self.status == other.status)
    
    def __hash__(self):
        """
        Returns a hash value for the Run instance.
        This is useful for using Run instances as keys in dictionaries or adding them to sets.
        Returns:
            int: Hash value of the Run instance.
        """
        return hash((self.target, self.run_name, self.start_ts, self.end_ts, self.status))