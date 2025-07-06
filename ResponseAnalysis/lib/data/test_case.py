# @author: Sudarsun
# @date: 2025-06-15
#
# This module defines the TestCase class, which represents a test case in the evaluation system.

from .prompt import Prompt
from .response import Response
from .llm_judge_prompt import LLMJudgePrompt
from typing import Optional, Any
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    """
    Represents a test case in the response analysis system.
    Attributes:
        name (str): The name of the test case.
        metric (str): The name of the metric associated with the test case.
        prompt (Prompt): The prompt associated with the test case.
        response (Response): The response associated with the test case.
        strategy (str|int): The strategy name or id used for the test case.
        judge_prompt (LLMJudgePrompt): The judge prompt for the test case, if applicable.
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    name: str = Field(..., description="The name of the test case.")
    metric: str = Field(..., description="The name of the metric associated with the test case.")
    prompt: Prompt = Field(..., description="The prompt for the test case.")
    response: Optional[Response] = Field(None, description="The response for the test case.")
    strategy: str = Field(..., description="The strategy name used for the test case")
    judge_prompt: Optional[LLMJudgePrompt] = Field(None, description="The judge prompt for the test case, if applicable.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility")
    
    def __init__(self, name:str, metric:str, prompt: Prompt, strategy: str|int, response: Optional[Response] = None, judge_prompt:Optional[LLMJudgePrompt]=None, **kwargs):
        """
        Initializes a TestCase instance.

        Args:
            metric (str): The name of the metric associated with the test case.
            name (str): The name of the test case.
            strategy (str|int): The strategy name or id used for the test case.
            judge_prompt (LLMJudgePrompt): The judge prompt for the test case, if applicable
            prompt (Prompt): The prompt for the test case.
            response (Response): The response for the test case.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(name =name, metric=metric, prompt = prompt, strategy=strategy, response=response, judge_prompt=judge_prompt, kwargs = kwargs)

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

    def evaluate(self) -> float:
        """
        Evaluates the test case.
        This method can be overridden by subclasses to provide specific evaluation logic.
        """
        raise NotImplementedError("someone should implement this method.")

    def __str__(self):
        """Returns a string representation of the test case."""
        return f"TestCase(prompt=\"{self.prompt}\", response=\"{self.response}\")"
    
    def __repr__(self):
        """Returns a string representation of the TestCase instance for debugging."""
        return f"TestCase(prompt=\"{self.prompt!r}\", response=\"{self.response!r}\")"
    
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