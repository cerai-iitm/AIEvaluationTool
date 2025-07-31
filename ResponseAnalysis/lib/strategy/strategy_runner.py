#   @author G Balayogi
#   @email balayogistark@gmail.com
#   @create date 2025-07-17 12:11:47
#   @modify date 2025-07-20
#   @desc Strategy runner code that executes strategies based on test plans and metrics.
#   It loads test plans, metric mappings, and agent responses from JSON files, and generates a consolidated score report.

from strategy_implementor import StrategyImplementor
from logger import get_logger
from utils import load_json, extract_score,get_key_by_value
from collections import defaultdict
import csv
from tabulate import tabulate
import pandas as pd
import argparse

logger = get_logger("strategy_runner")

plan_file = "Data/plans.json"
datapoints_file = "Data/datapoints_combined.json"
metric_to_strategy_mapping_file = "Data/metric_strategy_mapping.json"
strategy_id_to_strategy_mapping_file = "Data/strategy_id.json"

parser = argparse.ArgumentParser(description="LLM Startegy Runner - Runner which uses strategies to compute the metrics")
parser.add_argument("--response-file", "-r", dest="response_file", type=str, default="Data/responses_T3.json", help="Location of responses file for each test plan")
parser.add_argument("--test-plan-id", "-t", dest="test_plan_id", type=str, default="T3", help="The test plan ID to be analyzed")

args = parser.parse_args()

response_file = args.response_file

def get_agent_response_map(agent_responses, prompt_id):
    l = extract_prompt_ids_from_response(agent_responses)

    if prompt_id in l:
        for resp in agent_responses:
            if resp.get("prompt_id") == prompt_id:  # or however you identify prompt_id in resp
                return resp["response"]
    else:
        return "PROMPT NOT FOUND"

def get_metric_names_by_test_plan_id(test_plan_id, test_plans):
    if test_plan_id in test_plans:
        return [name.lower() for name in test_plans[test_plan_id]["metrics"].values()]
    else:
        return []

def extract_prompt_data(data, prompt_ids):
    new_data = []
    for i in data:
        if i["PROMPT_ID"] in prompt_ids:
            new_data.append(i)
    return new_data

def extract_prompt_ids_from_response(data):
    l = []
    for resp in data:
        l.append(resp["prompt_id"])
    return l

def run(target_plan_id):
    test_plans = load_json(plan_file)
    metric_to_test_case_mapping = load_json(datapoints_file)
    strategy_map = load_json(metric_to_strategy_mapping_file)
    agent_responses = load_json(response_file)
    strategy_id_to_strategy_map = load_json(strategy_id_to_strategy_mapping_file)
    fields = ["PROMPT_ID", "LLM_AS_JUDGE", "SYSTEM_PROMPT", "PROMPT", "EXPECTED_OUTPUT", "DOMAIN", "STRATEGY"]
    consolidated_scores={}

    #if target_plan_id != "T6":
    if target_plan_id in test_plans:
        plan = test_plans[target_plan_id]
        plan_name = plan["TestPlan_name"]
        metrics = plan["metrics"]

        all_cases = {}
        for metric_id, metric_name in metrics.items():
            logger.info(f"Gathering datapoints for metric id: {metric_id}")
            if metric_id not in ["47","48","41","44","50", "51"]:
                if metric_id in metric_to_test_case_mapping:
                    for case in metric_to_test_case_mapping[metric_id]["cases"]:
                        row = [target_plan_id, plan_name, metric_id, metric_name]
                        row += [case.get(field, "") for field in fields]
                        resp_prompts = extract_prompt_ids_from_response(agent_responses)
                        if row[4] in resp_prompts:
                            if metric_id not in all_cases:
                                all_cases[metric_id] = [row]
                            else:
                                all_cases[metric_id].append(row)
                            logger.info(f"PROMPT included! {row[4]}")
            else:
                logger.info("PROMPTS NOT REQUIRED!")
                all_cases[metric_id] = "PROMPTS NOT REQUIRED!"
            
            if all_cases[metric_id] != "PROMPTS NOT REQUIRED!":
                dl = []
                for data_list in all_cases[metric_id]:
                    dl.append(data_list[-1][-1])
                unique_strategy = set(dl)
            
                logger.info(f"Metric ID: {metric_id}")
                for us in unique_strategy:
                    logger.info(f"Unique Strategies: {us}")
                # break
                strategy_data_list = {}
                for data_list in all_cases[metric_id]:
                    for us in unique_strategy:
                        if us not in strategy_data_list:
                            agent_response = get_agent_response_map(agent_responses,data_list[4])
                            logger.info(f"For PromptID: {data_list[4]}, the Agent response is: {agent_response}")
                            if agent_response != "PROMPT NOT FOUND":
                                if data_list[10] == [us]: 
                                    strategy_data_list[us] = {
                                        "PROMPT": [data_list[7]],
                                        "EXPECTED_RESPONSES": [data_list[8]],
                                        "AGENT_RESPONSES": [agent_response],
                                        "SYSTEM_PROMPTS": [data_list[6]],
                                        "JUDGE_PROMPTS": [data_list[5]],
                                        "PROMPT_ID": [data_list[4]]
                                    }
                            else:
                                logger.info(f"PROMPT {data_list[4]} not included!")
                        else:
                            agent_response = get_agent_response_map(agent_responses,data_list[4])
                            logger.info(f"For PromptID: {data_list[4]}, the Agent response is: {agent_response}")
                            if agent_response != "PROMPT NOT FOUND":
                                if data_list[10] == [us]:
                                    strategy_data_list[us]["PROMPT"].append(data_list[7])
                                    strategy_data_list[us]["EXPECTED_RESPONSES"].append(data_list[8])
                                    strategy_data_list[us]["AGENT_RESPONSES"].append(agent_response)
                                    strategy_data_list[us]["SYSTEM_PROMPTS"].append(data_list[6])
                                    strategy_data_list[us]["JUDGE_PROMPTS"].append(data_list[5])
                                    strategy_data_list[us]["PROMPT_ID"].append(data_list[4])
                            else:
                                logger.info(f"PROMPT {data_list[4]} not included!")
                strategy_map_clean = {k: [v] for k, v in strategy_id_to_strategy_map.items()}
                strategy_names = [s for sid in unique_strategy if sid in strategy_map_clean for s in strategy_map_clean[sid]]
                st_scores= []
                for strategy_name in strategy_names:
                        st_id = get_key_by_value(strategy_id_to_strategy_map, strategy_name)
                        logger.info(f"The strategy ID which is executed is {st_id}")
                        logger.info(f"The strategy name to be executed {strategy_name}")
                        strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name.lower())
                        st_score = strategy_instance.execute(
                                        prompts=strategy_data_list[st_id]["PROMPT"],
                                        expected_responses=strategy_data_list[st_id]["EXPECTED_RESPONSES"],
                                        agent_responses=strategy_data_list[st_id]["AGENT_RESPONSES"],
                                        system_prompts=strategy_data_list[st_id]["SYSTEM_PROMPTS"],
                                        judge_prompts=strategy_data_list[st_id]["JUDGE_PROMPTS"]
                                    )
                        print("score: ",st_score)
                        logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {st_score}")
                        st_scores.append(st_score)
                        logger.info(f"List of scores: {st_scores}")
                
                consolidated_scores[metric_name] = sum(st_scores)/len(st_scores)
                logger.info(f"Consolidated Score - {consolidated_scores}")   
                
            else:
                st_scores = []
                strategy_names = strategy_map[metric_id]
                for strategy_name in strategy_names:
                    st_id = get_key_by_value(strategy_id_to_strategy_map, strategy_name)
                    logger.info(f"The strategy ID which is executed is {st_id}")
                    logger.info(f"The strategy name to be executed {strategy_name}")
                    strategy_instance = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name.lower())
                    st_score = strategy_instance.execute()
                    print("score: ",st_score)
                    logger.info(f"[SUCCESS] Strategy: {strategy_name}, Metric: {metric_name}, Score: {st_score}")
                st_scores.append(st_score)
                logger.info(f"List of scores: {st_scores}")
                    
        
            consolidated_scores[metric_name] = sum(st_scores)/len(st_scores)
            logger.info(f"Consolidated Score - {consolidated_scores}")


    plan_name = test_plans[target_plan_id]["TestPlan_name"]
    metrics = list(consolidated_scores.items())

    rows = []

    for i, (metric_name, score) in enumerate(metrics):
        rows.append([
            plan_name if i == 0 else "",  # Only first row has plan name
            metric_name,
            f"{score:.2f}"
        ])

    headers = ["Plan Name", "Metric Name", "Score"]

    print("\n=== Consolidated Score Report ===")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

    report_data = []
    for i, (metric_name, score) in enumerate(consolidated_scores.items()):
        report_data.append({
            "Plan Name": plan_name if i == 0 else "",
            "Metric Name": metric_name,
            "Score": round(score, 5)
        })

    # Create DataFrame
    df = pd.DataFrame(report_data)

    # Save to Excel
    output_path = f"evaluation_summary_{target_plan_id}.xlsx"
    df.to_excel(output_path, index=False)

    print(f"\n Evaluation Scores saved at: {output_path}")

# Example usage:
run(args.test_plan_id) 
