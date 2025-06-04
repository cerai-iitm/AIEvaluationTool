from .test_case import TestCase
from typing import List
from functools import reduce

class EvaluationMetric:
    """
    Base class for evaluation metrics.
    """

    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc

    def evaluate(self, test_cases: List[TestCase]) -> float:
        """
        Evaluate the test cases to compute a score.
        """
        # compute the total score by summing up the scores of each test case
        total = reduce(lambda x, y: x + y, [tc.evaluate() for tc in test_cases])
        # If there are no test cases, return 0.0 to avoid division by zero
        if len(test_cases) == 0:
            return 0.0
        # return the average score
        # This assumes that each test case contributes equally to the final score
        # If you want to weight them differently, you can modify this logic
        # accordingly. For example, you could use a weighted average based on some criteria.
        # Here, we simply return the average score.
        return total / len(test_cases)

    def __str__(self):
        return f"EvaluationMetric(name={self.name}, description={self.desc})"