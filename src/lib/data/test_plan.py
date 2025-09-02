# @author: Sudarsun S
# @date: 2025-06-20
# @version: 1.0.0
# Create a test plan that includes multiple evaluation metrics.
# @description: This module defines a TestPlan class that allows for the creation of test plans
# with multiple evaluation metrics. Each metric can be evaluated against test cases, and the results
# can be aggregated to provide an overall score for the test plan.
# @license: MIT License

from .evaluation_metric import Metric
from typing import Any, Optional, List
from pydantic import BaseModel, Field

class TestPlan(BaseModel):
    """
    Represents a test plan that includes multiple evaluation metrics.
    """
    plan_name: str = Field(..., description="The name of the test plan.")
    plan_description: Optional[str] = Field(None, description="A description of the test plan.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility.")
    metrics: List[Metric] = Field(default_factory=list, description="List of evaluation metrics associated with the test plan.")
    
    def __init__(self, plan_name: str, plan_description: Optional[str] = None, **kwargs):
        """
        Initializes a TestPlan instance.
        Args:
            name (str): The name of the test plan.
            desc (str): A description of the test plan.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(plan_name=plan_name, plan_description=plan_description, kwargs=kwargs)
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

    def add_metric(self, metric: Metric):
        """
        Add an evaluation metric to the test plan.
        """
        self.metrics.append(metric)

    def set_metrics(self, metrics: List[Metric]):
        """
        Set multiple evaluation metrics for the test plan.
        """
        if not isinstance(metrics, list):
            raise TypeError("Metrics should be a list of Metric instances.")
        self.metrics = metrics

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
        return f"TestPlan(name='{self.plan_name}', description='{self.plan_description}', metrics=\"{self.metrics}\")"