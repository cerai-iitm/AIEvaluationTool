from pydantic import BaseModel, Field
from typing import Any, Optional
import hashlib

class LLMJudgePrompt(BaseModel):
    """
    Represents a prompt used for judging responses in the response analysis system.
    Attributes:
        judge_prompt (str): The prompt to use while judging an AI agent response.
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    judge_prompt: str = Field(..., description="The prompt to use while judging an AI agent response.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")

    def __init__(self, judge_prompt: str, **kwargs):
        super().__init__(judge_prompt=judge_prompt, kwargs=kwargs)

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
    
    def __str__(self):
        """
        Returns a string representation of the judge prompt.
        """
        return f"Judge Prompt: '{self.judge_prompt}'"
    
    def __repr__(self):
        """
        Returns a string representation of the LLMJudgePrompt instance for debugging.
        """
        return f"LLMJudgePrompt(judge_prompt='{self.judge_prompt!r}')"
    
    def __eq__(self, other):
        """
        Checks equality between two LLMJudgePrompt instances.
        Compares the judge_prompt.
        """
        if not isinstance(other, LLMJudgePrompt):
            return False
        return self.judge_prompt == other.judge_prompt
    
    def __hash__(self):
        """
        Returns a hash of the LLMJudgePrompt instance.
        Uses the judge_prompt to generate a unique hash.
        """
        return hash(self.judge_prompt)
    
    @property
    def digest(self) -> str:
        """
        Returns a SHA-1 digest of the judge prompt.
        This can be used for quick comparisons or checksums.
        """
        return hashlib.sha1(self.judge_prompt.encode('utf-8')).hexdigest()