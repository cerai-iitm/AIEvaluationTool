#   @author G Balayogi
#   @email balayogistark@gmail.com
#   @create date 2025-07-17 12:11:47
#   @modify date 2025-07-17 12:11:47
#   @desc Strategy runner code that executes strategies based on test plans and metrics.
#   It loads test plans, metric mappings, and agent responses from JSON files.

from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json, get_key_by_value

logger = get_logger("strategy_runner")

plan_file = "Data/plans.json"
datapoints_file = "Data/new_data.json"
strategy_mapping_file = "Data/metric_strategy_mapping.json"
response_file = "Data/responses.json"

def get_agent_response_map(agent_responses):
    return {item["prompt_id"]: item["response"] for item in agent_responses}

def run(target_plan_id):
    test_plans = load_json(plan_file)
    metric_to_test_case_mapping = load_json(datapoints_file)
    strategy_map = load_json(strategy_mapping_file)
    agent_responses = load_json(response_file)

    fields = ["PROMPT_ID", "LLM_AS_JUDGE", "SYSTEM_PROMPT", "PROMPT", "EXPECTED_OUTPUT", "DOMAIN", "STRATEGY"]

    result_rows = []

    if target_plan_id in test_plans:
        plan = test_plans[target_plan_id]
        plan_name = plan["TestPlan_name"]
        metrics = plan["metrics"]

        for metric_id, metric_name in metrics.items():
            if metric_id in metric_to_test_case_mapping:
                for case_group in metric_to_test_case_mapping[metric_id]["cases"]:
                    for case in case_group:
                        row = [target_plan_id, plan_name, metric_id, metric_name]
                        row += [case.get(field, "") for field in fields]
                        result_rows.append(row)
    else:
        print(f"Test plan ID '{target_plan_id}' not found.")

    for i, row in enumerate(result_rows, 1):
        plan_id = row[0]
        plan_name = row[1]
        metric_id = row[2]
        metric_name = row[3]
        prompt_id = row[4]
        llm_as_judge = row[5]
        system_prompt = row[6]
        prompt = row[7]
        expected_output = row[8]
        domain = row[9]
        strategy = row[10]

        # To include unknown metrics
        # strategy_functions = [s for sid in strategy for s in strategy_map.get(sid, [f"Unknown({sid})"])]

        # To exclude unknown metrics
        strategy_functions = [s for sid in strategy if sid in strategy_map for s in strategy_map[sid]]

        agent_response_map = get_agent_response_map(agent_responses)

        if prompt_id not in agent_response_map:
            logger.warning(f"Prompt ID {prompt_id} not found in agent responses. Skipping execution.")
            continue

        agent_response = agent_response_map[prompt_id]

        for strategy_name in strategy_functions:
            print(f"Executing strategy: {strategy_name} for prompt ID: {prompt_id}")

            try:
                strategy_instance = StrategyImplementor(strategy_name=strategy_name)

                # logger.info(
                #     f"[RUNNING] strategy '{strategy_name}' on prompt ID '{prompt_id}, System Prompt: {system_prompt}, Prompt: {prompt}, Expected Response: {expected_output}, Agent Response: {agent_response}, LLM Judge: {llm_as_judge}"
                # )

                score = strategy_instance.execute(
                    prompts=[prompt],
                    expected_responses=[expected_output],
                    agent_responses=[agent_response],
                    system_prompts=[system_prompt],
                    judge_prompts=[llm_as_judge]
                )

                print(f"[SUCCESS] Strategy: {strategy_name}, Score: {score}")
                logger.info(f"[SUCCESS] Strategy: {strategy_name}, Score: {score}")

            except Exception as e:
                error_msg = f"[SKIPPED] Error in strategy '{strategy_name}' for prompt ID '{prompt_id}': {str(e)}"
                print(error_msg)
                logger.error(error_msg)
                continue


# Example usage:
run("T1") 
