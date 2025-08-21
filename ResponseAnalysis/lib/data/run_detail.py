#@author: Sudarsun
# @date: 2025-06-29
#
# This module defines the TestRunDetails class, which represents the details of a run in the AI evaluation system.

from pydantic import BaseModel, Field
from typing import Any

class RunDetail(BaseModel):
    """
    Represents the details of a test run.
    Attributes:
        run_name (str): Name of the test run, typically a unique identifier.
        plan_name (str): The name of the target application.
        metric_name (str): The name of the metric associated with the run.
        testcase_name (str): The name of the test case associated with the run.
        status (str): Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.
        kwargs (dict): Additional keyword arguments for future extensibility.
    """
    run_name: str = Field(..., description="Name of the test run, typically a unique identifier.")
    plan_name: str = Field(..., description="The name of the target application.")
    metric_name: str = Field(..., description="The name of the metric associated with the run.")
    testcase_name: str = Field(..., description="The name of the test case associated with the run.")
    status: str = Field(..., description="Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.")
    kwargs: dict = Field(default_factory=dict, description="Additional keyword arguments for future extensibility")

    def __init__(self, run_name: str, plan_name: str, metric_name: str, testcase_name: str, status: str = "NEW", **kwargs):
        """
        Initializes a RunDetail instance.
        Args:
            run_name (str): Name of the test run, typically a unique identifier.
            plan_name (str): The name of the target application.
            metric_name (str): The name of the metric associated with the run.
            testcase_name (str): The name of the test case associated with the run.
            status (str): Status of the run, e.g., 'completed', 'failed', 'running', or 'new'.
            kwargs: Additional keyword arguments for future extensibility.
        """
        super().__init__(run_name=run_name, plan_name=plan_name, metric_name=metric_name, testcase_name=testcase_name, status=status, kwargs=kwargs)

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
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self.kwargs.get(name)
    
    def __repr__(self):
        return f"RunDetail(run_name='{self.run_name}', plan_name='{self.plan_name}', metric_name='{self.metric_name}', testcase_name='{self.testcase_name}', status='{self.status}')" 
    
    def __str__(self):
        kwargs_str = ", ".join([f"{key}: '{value}'" for key, value in self.kwargs.items()])
        main_str = f"RunDetail with run_name: '{self.run_name}', plan_name: '{self.plan_name}', metric_name: '{self.metric_name}', testcase_name: '{self.testcase_name}', status: '{self.status}'"
        return f"{main_str}, additional attributes: {kwargs_str}" if kwargs_str else  main_str
    
    def __eq__(self, other):
        if not isinstance(other, RunDetail):
            return False
        return (self.run_name == other.run_name and
                self.plan_name == other.plan_name and
                self.metric_name == other.metric_name and
                self.testcase_name == other.testcase_name and
                self.status == other.status)
    
    def __hash__(self):
        return hash((self.run_name, self.plan_name, self.metric_name, self.testcase_name, self.status))
    