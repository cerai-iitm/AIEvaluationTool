#   @author G Balayogi
#   @email balayogistark@gmail.com
#   @create date 2025-07-17 12:11:47
#   @modify date 2025-07-20
#   @desc Strategy runner code that executes strategies based on test plans and metrics.
#   It loads test plans, metric mappings, and agent responses from JSON files, and generates a consolidated score report.

from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json, extract_score
from collections import defaultdict
import csv

logger = get_logger("strategy_runner")

plan_file = "Data/plans.json"
datapoints_file = "Data/datapoints_old_metrics.json"
metric_to_strategy_mapping_file = "Data/metric_strategy_mapping.json"
strategy_id_to_strategy_mapping_file = "Data/strategy_id.json"
response_file = "Data/responses_T6_Large_old.json"

def get_agent_response_map(agent_responses):
    return {item["prompt_id"]: item["response"] for item in agent_responses}

def get_metric_names_by_test_plan_id(test_plan_id, test_plans):
    if test_plan_id in test_plans:
        return [name.lower() for name in test_plans[test_plan_id]["metrics"].values()]
    else:
        return []

def run(target_plan_id):
    test_plans = load_json(plan_file)
    metric_to_test_case_mapping = load_json(datapoints_file)
    strategy_map = load_json(metric_to_strategy_mapping_file)
    agent_responses = load_json(response_file)
    strategy_id_to_strategy_map = load_json(strategy_id_to_strategy_mapping_file)

    agent_response_map = get_agent_response_map(agent_responses)
    metric_scores = defaultdict(list)
    fields = ["PROMPT_ID", "LLM_AS_JUDGE", "SYSTEM_PROMPT", "PROMPT", "EXPECTED_OUTPUT", "DOMAIN", "STRATEGY"]

    if target_plan_id != "T6":
        if target_plan_id in test_plans:
            plan = test_plans[target_plan_id]
            plan_name = plan["TestPlan_name"]
            metrics = plan["metrics"]

            for metric_id, metric_name in metrics.items():
                if metric_id in metric_to_test_case_mapping:
                    for case in metric_to_test_case_mapping[metric_id]["cases"]:
                        row = [target_plan_id, plan_name, metric_id, metric_name]
                        row += [case.get(field, "") for field in fields]

                        prompt_id = row[4]
                        llm_as_judge = row[5]
                        system_prompt = row[6]
                        prompt = row[7]
                        expected_output = row[8]
                        strategy_ids = row[10]

                        if prompt_id not in agent_response_map:
                            logger.warning(f"Prompt ID {prompt_id} not found in agent responses. Skipping execution.")
                            continue

                        # Convert strategy_ids to strategy names
                        strategy_id_list = strategy_ids if isinstance(strategy_ids, list) else [strategy_ids]
                        strategy_map_clean = {k: [v] for k, v in strategy_id_to_strategy_map.items()}
                        strategy_names = [s for sid in strategy_id_list if sid in strategy_map_clean for s in strategy_map_clean[sid]]

                        agent_response = agent_response_map[prompt_id]
                        for strategy_name in strategy_names:
                            try:
                                strategy_instance = StrategyImplementor(strategy_name=strategy_name)
                                score = strategy_instance.execute(
                                    prompts=[prompt],
                                    expected_responses=[expected_output],
                                    agent_responses=[agent_response],
                                    system_prompts=[system_prompt],
                                    judge_prompts=[llm_as_judge]
                                )
                                logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                                metric_scores[metric_name].append(score)
                            except Exception as e:
                                logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")
                                continue
        else:
            logger.error(f"Test plan ID '{target_plan_id}' not found.")
    else:
        plan_name = test_plans[target_plan_id]["TestPlan_name"]
        performance_metrics = get_metric_names_by_test_plan_id(test_plan_id=target_plan_id, test_plans=test_plans)
        tat_tpm_mvh_metrics = [performance_metrics[0], performance_metrics[4], performance_metrics[5]]
        tat_tpm_mvh_strategy_names = ['tat_tpm_mvh']
        other_strategy_names = ["uptime_calculation", "compute_error_rate", "compute_mtbf"]
        other_metrics = [performance_metrics[1], performance_metrics[2], performance_metrics[3]]

        executed_pairs = set()
        executed_strategies = []

        # TAT, TPM, MVH execution
        for strategy_name in tat_tpm_mvh_strategy_names:
            for metric_name in tat_tpm_mvh_metrics:
                pair = (strategy_name, metric_name)
                if pair in executed_pairs:
                    continue
                try:
                    logger.info(f"Executing strategy: {strategy_name} for metric: {metric_name}")
                    strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
                    score = strategy_instance.execute()
                    metric_scores[metric_name].append(score)
                    executed_pairs.add(pair)
                    logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                except Exception as e:
                    logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")

        # Other metric executions
        for strategy_name, metric_name in zip(other_strategy_names, other_metrics):
            if strategy_name in executed_strategies:
                continue
            try:
                if strategy_name == "privacy_strategy":
                    # Special handling for privacy strategy
                    for metric_name in special_metrics[-3:]:
                        # print(f"Executing privacy strategy for metric: {metric_name}")
                        strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
                        score = strategy_instance.execute(expected_responses=[expected_output],agent_responses=[agent_response],system_prompts=[system_prompt],prompts = [prompt])
                        print(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                        logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                elif strategy_name == "safety_strategy":
                    # Special handling for safety strategy
                    for metric_name in special_metrics[:3]:
                        # print(f"Executing safety strategy for metric: {metric_name}")
                        strategy_instance = StrategyImplementor(strategy_name=strategy_name,metric_name=metric_name )
                        score = strategy_instance.execute(agent_responses=[agent_response] ,prompts = [prompt])
                        print(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                        logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
                else:
#                     strategy_instance = StrategyImplementor(strategy_name=strategy_name)
#                     score = strategy_instance.execute(
#                         prompts=[prompt],
#                         expected_responses=[expected_output],
#                         agent_responses=[agent_response],
#                         system_prompts=[system_prompt],
#                         judge_prompts=[llm_as_judge]
#                     )

#                     print(f"[SUCCESS] Strategy: {strategy_name}, Score: {score}")
#                     logger.info(f"[SUCCESS] Strategy: {strategy_name}, Score: {score}")

                      logger.info(f"Executing strategy: {strategy_name} for metric: {metric_name}")
                      strategy_instance = StrategyImplementor(strategy_name=strategy_name)
                      score = strategy_instance.execute()
                      metric_scores[metric_name].append(score)
                      executed_strategies.append(strategy_name)
                      logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {score}")
            
            except Exception as e:
                logger.error(f"[SKIPPED] Error in strategy '{strategy_name}' for metric '{metric_name}': {str(e)}")

    
    # ===== Consolidated Report Output =====
    print("\n=== Consolidated Report ===")
    print("{:<20} {:<30} {:<10}".format("Plan Name", "Metric Name", "Score"))
    print("-" * 60)
    for metric_name, scores in metric_scores.items():
        numeric_scores = [extract_score(s) for s in scores]
        avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0
        print("{:<20} {:<30} {:<10.2f}".format(test_plans[target_plan_id]["TestPlan_name"], metric_name, avg_score))

    # Optional: Save to CSV
    with open("consolidated_report.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Plan Name", "Metric Name", "Score"])
        for metric_name, scores in metric_scores.items():
            numeric_scores = [extract_score(s) for s in scores]
            avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0
            writer.writerow([test_plans[target_plan_id]["TestPlan_name"], metric_name, f"{avg_score:.2f}"])



# Example usage:
run("T5") 
