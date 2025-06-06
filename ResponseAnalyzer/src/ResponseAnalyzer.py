
import os
import json
import asyncio
from strategies import (
    language_coverage,
    language_coverage_similarity,
    llm_as_judge,
    text_similarity,
    toxicity_model_result,
    grammarcheck,
    lexical_diversity,
    bleu_score_metric,
    meteor_metric,
    rouge_score_metric
)

from pathlib import Path

current_file = Path(__file__).resolve()

# Setting path to the Data folder
plans_path = current_file.parents[2] / "Data" / "plans.json"

data_points_path = current_file.parents[2] / "Data" / "DataPoints.json"

response_path = current_file.parents[2] / "Data" / "responses.json"

strategy_map_path = current_file.parents[2] / "Data" / "strategy_map.json"

response_analyzer_results_path = current_file.parents[2] / "Data" / "response_analysis_output.json"

with open(data_points_path, 'r',encoding='utf-8') as f:
    datapoints = json.load(f)

with open(plans_path, 'r') as f:
    plans = json.load(f)

with open(response_path, 'r',encoding='utf-8') as f:
    responses = json.load(f)

with open(strategy_map_path, 'r') as f:
    strategy_map = json.load(f)

strategy_functions = {
    "language_coverage": language_coverage,
    "language_coverage_similarity": language_coverage_similarity,
    "llm_as_judge": llm_as_judge,
    "text_similarity": text_similarity,
    "toxicity_model_result": toxicity_model_result,
    "grammarcheck": grammarcheck,
    "lexical_diversity": lexical_diversity,
    "bleu_score_metric": bleu_score_metric,
    "meteor_metric": meteor_metric,
    "rouge_score_metric": rouge_score_metric
}


final_results = {}


test_plan_groups = {}
for item in responses:
    plan_id = item["test_plan_id"]
    test_plan_groups.setdefault(plan_id, []).append(item)

async def analyze():
    for plan_id, response_items in test_plan_groups.items():
        plan_info = plans.get(plan_id, {})
        plan_name = plan_info.get("TestPlan_name", f"UnknownPlan_{plan_id}")
        final_results.setdefault(plan_name, {"metrics": {}})
        metrics = plan_info.get("metrics", {})

        for metric_id, metric_name in metrics.items():
            failed_cases = 0
            collected_prompts = []
            collected_responses = []
            expected_outputs = []
            sys_prompts = []

            for resp_item in response_items:
                prompt_id = resp_item.get("prompt_id")
                response_text = resp_item.get("response", "").strip()
                
                
                if not response_text:
                    failed_cases += 1
                    continue

                
                dp_case = None
                for case in datapoints.get(metric_id, {}).get("cases", []):
                    if case["PROMPT_ID"] == prompt_id:
                        dp_case = case
                        break

                if not dp_case:
                    failed_cases += 1
                    continue

                collected_prompts.append(dp_case["PROMPT"])
                collected_responses.append(response_text)
                expected_outputs.append(dp_case.get("EXPECTED_OUTPUT", ""))
                sys_prompts.append(dp_case.get("SYSTEM_PROMPT", ""))

      
            strategy_fn = None
            for strat_id, strat in strategy_map.items():
                if metric_id in strat["metrics"]:
                    strategy_fn = strategy_functions.get(strat["name"])
                    break

            
            score = None

            try:
                if strategy_fn:
                    if strategy_fn.__name__ in ["language_coverage", "grammarcheck", "lexical_diversity"]:
                        score = await strategy_fn(collected_prompts, collected_responses)
                    elif strategy_fn.__name__ == "language_coverage_similarity":
                        score = await strategy_fn(collected_prompts, collected_responses, expected_outputs)
                    elif strategy_fn.__name__ == "llm_as_judge":
                        score = strategy_fn(
                            metric_name=metric_name,
                            task_intro="Evaluate the LLM response",
                            judge_prompt="Check if the response aligns with expectations",
                            system_prompt=sys_prompts[0] if sys_prompts else "",
                            prompts=collected_prompts,
                            test_case_response=collected_responses[0] if collected_responses else "",
                            expected_response=expected_outputs[0] if expected_outputs else ""
                        )
                    elif strategy_fn.__name__ in ["text_similarity", "bleu_score_metric", "meteor_metric", "rouge_score_metric"]:
                        score = strategy_fn(collected_prompts, collected_responses, expected_outputs)
                    elif strategy_fn.__name__ == "toxicity_model_result":
                        score = strategy_fn(collected_responses)
                        print(score)
                    if isinstance(score, list) and score:
                        score = round(sum(score) / len(score), 3)
                    elif isinstance(score, (int, float)):
                        score = round(score, 3)
                    else:
                        score = None
                else:
                    print(f"No strategy function mapped for metric: {metric_name}")
            except Exception as e:
                print(f"[ERROR] Metric {metric_name} - {str(e)}")
                score = None

            final_results[plan_name]["metrics"][metric_name] = {
                "score": score,
                "failed_cases": failed_cases
            }

asyncio.run(analyze())

output_path = str(response_analyzer_results_path)
with open(output_path, "w") as f:
    json.dump(final_results, f, indent=2)

print(f"[INFO] Results saved to: {output_path}")
