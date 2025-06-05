from .evaluation_metric import EvaluationMetric

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
        return f"TestPlan(name={self.name}, description={self.desc}, metrics={self.metrics})"