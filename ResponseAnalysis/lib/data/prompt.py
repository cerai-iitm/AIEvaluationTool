from pydantic import BaseModel, Field
from typing import Optional

class Prompt(BaseModel):
    """
    Represents a prompt used in the response analysis system.
    Attributes:
        prompt (str): The text of the prompt.
    """
    system_prompt: Optional[str] = Field(None, description="The system prompt, if any.")
    user_prompt: Optional[str] = Field(None, description="The text of the prompt.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, system_prompt: Optional[str] = None, user_prompt: Optional[str] = None, **kwargs):
        """
        Initializes a Prompt instance.

        Args:
            system_prompt (Optional[str]): The system prompt, if any.
            user_prompt (Optional[str]): The text of the prompt.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(system_prompt=system_prompt, user_prompt=user_prompt, kwargs=kwargs)

    def __str__(self):
        """
        Returns a string representation of the prompt.
        If system_prompt is provided, it includes both system and user prompts.
        Otherwise, it returns only the user prompt.
        """
        if self.system_prompt:
            return f"System: {self.system_prompt}\nUser: {self.user_prompt}"
        return self.user_prompt
    
    def __repr__(self):
        """
        Returns a string representation of the Prompt instance for debugging.
        """
        return f"Prompt(system_prompt={self.system_prompt!r}, user_prompt={self.user_prompt!r})"
    
    def __eq__(self, other):
        """
        Checks equality between two Prompt instances.
        Compares both system_prompt and user_prompt.
        """
        if not isinstance(other, Prompt):
            return False
        return (self.system_prompt == other.system_prompt and
                self.user_prompt == other.user_prompt)
    
    def __hash__(self):
        """
        Returns a hash of the Prompt instance.
        Uses the hash of both system_prompt and user_prompt.
        """
        return hash((self.system_prompt, self.user_prompt))

    class Config:
        """Configuration for the Pydantic model."""
        extra = "forbid"
        allow_mutation = False
        frozen = True
        validate_assignment = True
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            str: lambda v: v,
            int: lambda v: v,
            float: lambda v: v,
            bool: lambda v: v,
        }
