from .test_case import TestCase
from typing import List, Optional
from functools import reduce

class EvaluationMetric:
    """
    Base class for evaluation metrics.
    """

    def __init__(self, name: str, desc: Optional[str] = None, **kwargs):
        """
        Initializes an EvaluationMetric instance.
        Args:
            name (str): The name of the evaluation metric.
            desc (str): A description of the evaluation metric.
            kwargs: Additional keyword arguments for future extensibility.
        """
        self.name = name
        self.desc = desc
        self.kwargs = kwargs
        self.test_cases = []  # List to hold test cases for this metric 

    def add_test_case(self, test_case: TestCase):
        """
        Add a test case to the evaluation metric.
        This method can be overridden by subclasses if needed.
        """
        self.test_cases.append(test_case)

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
        return f"EvaluationMetric(name={self.name}, description={self.desc})"