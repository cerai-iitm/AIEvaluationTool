# @author: Sudarsun S
# @date: 2025-06-20
# @version: 1.0.0
# @description: This module defines a base class for evaluation metrics used in the response analysis system.
# @license: MIT License

from .test_case import TestCase
from typing import List, Optional, Any
from functools import reduce
from pydantic import BaseModel, Field

class Metric(BaseModel):
    """
    Base class for evaluation metrics.
    """

    metric_name: str = Field(..., description="The name of the evaluation metric.")
    metric_description: Optional[str] = Field(None, description="A description of the evaluation metric.")
    domain_id: int = Field(..., description="The ID of the domain to which this metric belongs.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")
    test_cases: List[TestCase] = Field(default_factory=list, description="List of test cases associated with this metric.")

    def __init__(self, metric_name: str, domain_id: int, metric_description: Optional[str] = None, **kwargs):
        """
        Initializes an EvaluationMetric instance.
        Args:
            name (str): The name of the evaluation metric.
            desc (str): A description of the evaluation metric.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(metric_name=metric_name, domain_id = domain_id, metric_description=metric_description, kwargs=kwargs)
        self.test_cases = []  # List to hold test cases for this metric

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

    def add_test_case(self, test_case: TestCase):
        """
        Add a test case to the evaluation metric.
        This method can be overridden by subclasses if needed.
        """
        self.test_cases.append(test_case)

    def set_testcases(self, test_cases: List[TestCase]):
        """
        Set multiple test cases for the evaluation metric.
        This method can be overridden by subclasses if needed.
        """
        if not isinstance(test_cases, list):
            raise TypeError("test_cases must be a list of TestCase instances")
        self.test_cases = test_cases

    def evaluate(self) -> float:
        """
        Evaluate the test cases to compute a score.
        """
        # If there are no test cases, return 0.0 to avoid division by zero
        if len(self.test_cases) == 0:
            return 0.0
        
        # compute the total score by summing up the scores of each test case
        total = reduce(lambda x, y: x + y, [tc.evaluate() for tc in self.test_cases])
        # return the average score
        # This assumes that each test case contributes equally to the final score
        # If you want to weight them differently, you can modify this logic
        # accordingly. For example, you could use a weighted average based on some criteria.
        # Here, we simply return the average score.
        return total / len(self.test_cases)

    def __str__(self):
        return f"EvaluationMetric(name={self.metric_name}, description={self.metric_description})"
    
    def __repr__(self):
        return f"EvaluationMetric(metric_name='{self.metric_name}', domain_id={self.domain_id}, metric_description='{self.metric_description}')"