from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json, get_key_by_value

mapper = load_json("Data/metric_strategy_mapping.json")

print("Mapper loaded:", mapper)

plans = load_json("Data/plans.json")

print("Plans loaded:", plans)

datapoints = load_json("Data/DataPoints.json")

print("Data points loaded:", datapoints)

responses = load_json("Data/Responses.json")

print("Responses loaded:", responses)

logger = get_logger("strategy_runner")

class StrategyRunner:
    """
    StrategyRunner is responsible for running the strategies based on the plans and metric mappings.
    """
    def __init__(self, plan_name: str, **kwargs) -> None:
        self.plan_name = plan_name


    # Please start from here!
    # def get_plans(self, plan_name: str):
    #     """
    #     Get the plans based on the plan name.
    #     """
    #     if plan_name not in plans:
    #         logger.error(f"Plan {plan_name} not found.")
    #         return []
    #     else:
    #         logger.info(f"Loading plan: {plan_name}.")
    #         return plans[plan_name]

    def data_loader(self, metric_id):
        """
        Load the data points and return them.
        """
        if metric_id not in datapoints:
            logger.error(f"Metric ID {metric_id} not found in data points.")
            return []
        else:
            logger.info(f"Loading data points for metric ID {metric_id}.")
            return datapoints[metric_id]["cases"]
    
    def extract_data_from_datapoints(self, list_of_datapoints):
        """
        Extract system prompts, agent responses, and expected responses from the list of data points.
        """
        prompt_ids = []
        judge_prompts = []
        system_prompts = []
        prompts = []
        expected_responses = []
        domain = []
        
        for datapoint in list_of_datapoints:
            prompt_ids.append(datapoint.get("prompt_id", ""))
            judge_prompts.append(datapoint.get("judge_prompt", ""))
            prompts.append(datapoint.get("prompt", ""))
            domain.append(datapoint.get("domain", ""))
            system_prompts.append(datapoint.get("system_prompt", ""))
            expected_responses.append(datapoint.get("expected_response", ""))
        
        return {
            "prompt_ids": prompt_ids,
            "judge_prompts": judge_prompts,
            "system_prompts": system_prompts,
            "prompts": prompts,
            "expected_responses": expected_responses,
            "domain": domain
        }
    
    def extract_responses(self, responses):
        """
        Extract agent responses from the responses data.
        """
        agent_responses = []
        for response in responses:
            agent_responses.append(response.get("response", ""))
            prompt_id = response.get("prompt_id", "")
        return {prompt_id:agent_responses}
    
    def data_mapper(self, datapoints, response_datapoints):
        """
        Map the data points to the responses based on the prompt ID.
        """
        mapped_data = []
        dp_prompts = datapoints["prompt_ids"]
        for i in range(len(dp_prompts)):
            if i == response_datapoints[f"{dp_prompts[i]}"]:
                mapped_data.append({
                    "prompt_id": dp_prompts[i],
                    "system_prompt": datapoints["system_prompts"][i],
                    "agent_response": response_datapoints[f"{dp_prompts[i]}"],
                    "expected_response": datapoints["expected_responses"][i],
                    "judge_prompt": datapoints["judge_prompts"][i],
                    "domain": datapoints["domain"][i]
                })
        return mapped_data

    
    # def run(self, plan_name:str):
    #     plan_name = self.plan_name
    #     plan_id = get_key_by_value(plans, plan_name)
    #     strategies = mapper[plan_id]
    #     metric_data = self.data_loader(plan_id)
    #     if plan_id=="54" or plan_id=="66":
    #         for strategy_name in strategies:
    #             strategy_instance = StrategyImplementor(strategy_name=strategy_name)
    #             score = strategy_instance.execute(prompts: da, expected_responses: Optional[List[str]] = None, agent_responses: Optional[List[str]] = None, system_prompts: Optional[List[str]] = None, judge_prompts: Optional[List[str]] = None)
    #             logger.info(f"Strategy: {strategy_name}, Score: {score}")

