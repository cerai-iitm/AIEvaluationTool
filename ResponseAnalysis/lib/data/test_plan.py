from .evaluation_metric import EvaluationMetric
from typing import Any, List

class TestPlan:
    """
    Represents a test plan that includes multiple evaluation metrics.
    """

    def __init__(self, name: str, desc: str, **kwargs):
        """
        Initializes a TestPlan instance.
        Args:
            name (str): The name of the test plan.
            desc (str): A description of the test plan.
            kwargs: Additional keyword arguments for future extensibility.
        """
        self.kwargs = kwargs
        self.name = name
        self.desc = desc
        self.metrics = []

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

    def add_metric(self, metric: EvaluationMetric):
        """
        Add an evaluation metric to the test plan.
        """
        self.metrics.append(metric)

    def evaluate(self):
        """
        Evaluate all metrics against the provided test cases.
        Returns a dictionary with metric names and their scores.
        """
        results = {}
        for metric in self.metrics:
            results[metric.name] = metric.evaluate()
        return results

    def __str__(self):
        return f"TestPlan(name=\"{self.name}\", description=\"{self.desc}\", metrics=\"{self.metrics}\")"