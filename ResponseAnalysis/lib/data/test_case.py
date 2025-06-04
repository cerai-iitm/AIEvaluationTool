from .prompt import Prompt
from .response import Response
from typing import Optional

class TestCase:
    """
    Represents a test case in the response analysis system.
    Attributes:
        prompt (Prompt): The prompt associated with the test case.
        response (Response): The response associated with the test case.
    """
    
    def __init__(self, prompt: Prompt, response: Optional[Response] = None):
        """
        Initializes a TestCase instance.

        Args:
            prompt (Prompt): The prompt for the test case.
            response (Response): The response for the test case.
        """
        self.prompt = prompt
        self.response = response

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