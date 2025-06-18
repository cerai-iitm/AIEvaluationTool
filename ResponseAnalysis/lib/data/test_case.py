from .prompt import Prompt
from .response import Response
from typing import Optional
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    """
    Represents a test case in the response analysis system.
    Attributes:
        name (str): The name of the test case.
        prompt (Prompt): The prompt associated with the test case.
        response (Response): The response associated with the test case.
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    name: str = Field(..., description="The name of the test case.")
    prompt: Prompt = Field(..., description="The prompt for the test case.")
    response: Optional[Response] = Field(None, description="The response for the test case.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility")
    
    def __init__(self, name:str, prompt: Prompt, response: Optional[Response] = None, **kwargs):
        """
        Initializes a TestCase instance.

        Args:
            prompt (Prompt): The prompt for the test case.
            response (Response): The response for the test case.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(name =name, prompt = prompt, response=response, kwargs = kwargs)

    def evaluate(self) -> float:
        """
        Evaluates the test case.
        This method can be overridden by subclasses to provide specific evaluation logic.
        """
        raise NotImplementedError("someone should implement this method.")

    def __str__(self):
        """Returns a string representation of the test case."""
        return f"TestCase(prompt={self.prompt}, response={self.response})"
    
    def __repr__(self):
        """Returns a string representation of the TestCase instance for debugging."""
        return f"TestCase(prompt={self.prompt!r}, response={self.response!r})"
    
    def __eq__(self, other):
        """
        Checks equality between two TestCase instances.
        Compares both prompt and response.
        """
        if not isinstance(other, TestCase):
            return False
        return (self.prompt == other.prompt and
                self.response == other.response)
    
    def __hash__(self):
        """
        Returns a hash of the TestCase instance.
        Uses the hash of both prompt and response.
        """
        return hash((self.prompt, self.response))