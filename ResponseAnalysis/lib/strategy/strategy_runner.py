#   @author G Balayogi
#   @email balayogistark@gmail.com
#   @create date 2025-07-17 12:11:47
#   @modify date 2025-07-17 12:11:47
#   @desc Strategy runner code that executes strategies based on test plans and metrics.
#   It loads test plans, metric mappings, and agent responses from JSON files.

from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json
from collections import defaultdict

logger = get_logger("strategy_runner")

plan_file = "Data/plans.json"
datapoints_file = "Data/ai_eval_new.json"
metric_to_strategy_mapping_file = "Data/metric_strategy_mapping.json"
strategy_id_to_strategy_mapping_file = "Data/strategy_id.json"
response_file = "Data/responses_T1.json"

def get_agent_response_map(agent_responses):
    return {item["prompt_id"]: item["response"] for item in agent_responses}
  
def get_metric_names_by_test_plan_id(test_plan_id, test_plans):
    if test_plan_id in test_plans:
        return [name.lower() for name in test_plans[test_plan_id]["metrics"].values()]
    else:
        return []

def run(target_plan_id):
    if target_plan_id != "T6":
        test_plans = load_json(plan_file)
        metric_to_test_case_mapping = load_json(datapoints_file)
        strategy_map = load_json(metric_to_strategy_mapping_file)
        agent_responses = load_json(response_file)
        strategy_id_to_strategy_map = load_json(strategy_id_to_strategy_mapping_file)

        fields = ["PROMPT_ID", "LLM_AS_JUDGE", "SYSTEM_PROMPT", "PROMPT", "EXPECTED_OUTPUT", "DOMAIN", "STRATEGY"]

        result_rows = []

        if target_plan_id in test_plans:
            plan = test_plans[target_plan_id]
            plan_name = plan["TestPlan_name"]
            metrics = plan["metrics"]

            for metric_id, metric_name in metrics.items():
                if metric_id in metric_to_test_case_mapping:
                    for case in metric_to_test_case_mapping[metric_id]["cases"]:
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
            strategy_map = {k: [v] for k, v in strategy_id_to_strategy_map.items()}
            strategy_functions = [s for sid in strategy if sid in strategy_map for s in strategy_map[sid]]

            agent_response_map = get_agent_response_map(agent_responses)

            if prompt_id not in agent_response_map:
                logger.warning(f"Prompt ID {prompt_id} not found in agent responses. Skipping execution.")
                continue

            agent_response = agent_response_map[prompt_id]
            special_metrics = get_metric_names_by_test_plan_id(test_plan_id=target_plan_id, test_plans=test_plans)
            
            for strategy_name in strategy_functions:
                print(f"Executing strategy: {strategy_name} for prompt ID: {prompt_id}")

                try:
                    if strategy_name == "privacy_strategy":
                        # Special handling for privacy strategy
                        for metric_name in special_metrics[-3:]:
                            logger.info(f"Executing privacy strategy for metric: {metric_name}")
                            strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
                            score = strategy_instance.execute(
                                expected_responses=[expected_output],
                                agent_responses=[agent_response],
                                system_prompts=[system_prompt]
                            )
                            logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                    elif strategy_name == "safety_strategy":
                        # Special handling for safety strategy
                        for metric_name in special_metrics[:3]:
                            # print(f"Executing safety strategy for metric: {metric_name}")
                            strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
                            score = strategy_instance.execute(
                                agent_responses=[agent_response]
                            )
                            logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                except Exception as e:
                    logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")
                    continue

    else:
        test_plans = load_json(plan_file)
        metric_to_test_case_mapping = load_json(datapoints_file)
        strategy_map = load_json(metric_to_strategy_mapping_file)
        agent_responses = load_json(response_file)
        strategy_id_to_strategy_map = load_json(strategy_id_to_strategy_mapping_file)
        executed_pairs = set()
        metric_scores = defaultdict(list)
        performance_metrics = get_metric_names_by_test_plan_id(test_plan_id=target_plan_id, test_plans=test_plans)
        tat_tpm_mvh_metrics = [performance_metrics[0], performance_metrics[4], performance_metrics[5]]

        tat_tpm_mvh_strategy_names = ['tat_tpm_mvh']
        other_strategy_names = ["uptime_calculation", "compute_error_rate", "compute_mtbf"]
        other_metrics = [performance_metrics[1], performance_metrics[2], performance_metrics[3]]

        # Execute TAT, TPM, and MVH strategies for specific metrics
        for strategy_name in tat_tpm_mvh_strategy_names:
            for metric_name in performance_metrics:
                if metric_name not in tat_tpm_mvh_metrics:
                    continue

                pair = (strategy_name, metric_name)
                if pair in executed_pairs:
                    continue

                logger.info(f"Executing strategy: {strategy_name} for metric: {metric_name}")
                executed_pairs.add(pair)

                try:
                    strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
                    score = strategy_instance.execute()
                    metric_scores[metric_name].append(score)
                    logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                except Exception as e:
                    logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")
                    continue

        # Execute other strategies for the remaining metrics
        executed_strategies = []
        other_strategy_map = dict(zip(other_strategy_names, other_metrics))
        print(other_strategy_map)

        for strategy_name, metric_name in other_strategy_map.items():
            if strategy_name in executed_strategies:
                print(strategy_name)
                logger.debug(f"[SKIPPED] Strategy '{strategy_name}' already executed.")
                continue

            if metric_name not in other_metrics:
                continue

            logger.info(f"Executing strategy: {strategy_name} for metric: {metric_name}")

            try:
                strategy_instance = StrategyImplementor(strategy_name=strategy_name)
                score = strategy_instance.execute()
                metric_scores[metric_name].append(score)
                logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
            except Exception as e:
                logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")
                continue

            executed_strategies.append(strategy_name)

# Example usage:
run("T1") 
