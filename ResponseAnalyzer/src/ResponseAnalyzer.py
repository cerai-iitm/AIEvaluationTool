import os
import json
import asyncio
import logging
import textwrap
import csv
from tabulate import tabulate
from colorama import Fore, Style, init
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
init(autoreset=True)

litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

file_handler = logging.FileHandler("analyzer_log.log", mode='w', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(logging.WARNING)

with open('../../Data/DataPoints.json', 'r', encoding='utf-8') as f:
    datapoints = json.load(f)
with open('../../Data/plans.json', 'r', encoding='utf-8') as f:
    plans = json.load(f)
with open('../../Data/responses.json', 'r', encoding='utf-8') as f:
    responses = json.load(f)
with open('../../Data/strategy_map.json', 'r', encoding='utf-8') as f:
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

test_plan_groups = {}
for item in responses:
    plan_id = item.get("test_plan_id")
    if plan_id is not None:
        test_plan_groups.setdefault(plan_id, []).append(item)

final_results = {}

# -----------------------Main analysis function --------------------------------------------------------
async def analyze():
    for plan_id, response_items in test_plan_groups.items():
        plan_info = plans.get(plan_id, {})
        plan_name = plan_info.get("TestPlan_name", f"UnknownPlan_{plan_id}")
        final_results.setdefault(plan_name, {"metrics": {}})
        metrics = plan_info.get("metrics", {})
        logger.info(f"---- Starting Test Plan: {plan_name} ----")
        print(f"\n---- Test Plan: {plan_name} ----")

        for metric_id, metric_name in metrics.items():
            collected_prompts, collected_responses, expected_outputs, sys_prompts = [], [], [], []
            evaluable_cases = 0
            for resp_item in response_items:
                prompt_id = resp_item.get("prompt_id")
                response_text = resp_item.get("response", "").strip()
                if not response_text:
                    continue

                dp_case = next(
                    (case for case in datapoints.get(metric_id, {}).get("cases", [])
                     if case.get("PROMPT_ID") == prompt_id),
                    None
                )
                if not dp_case:
                    continue

                evaluable_cases += 1
                collected_prompts.append(dp_case.get("PROMPT", ""))
                collected_responses.append(response_text)
                expected_outputs.append(dp_case.get("EXPECTED_OUTPUT", ""))
                sys_prompts.append(dp_case.get("SYSTEM_PROMPT", ""))

            if evaluable_cases == 0:
                final_results[plan_name]["metrics"][metric_name] = {
                    "score": None,
                    "failed_cases": 0,
                    "successful_cases": 0,
                    "note": "No matching prompts or valid responses found."
                }
                logger.warning(f"[{metric_name}] => Skipped. Reason: No matching prompts or valid responses found.")
                print(f"[{metric_name}] => (Skipped - Reason: No matching prompts or valid responses found.)")
                continue

            strategy_fn = None
            for strat_id, strat in strategy_map.items():
                if metric_id in strat.get("metrics", []):
                    strategy_fn = strategy_functions.get(strat.get("name"))
                    break

            if not strategy_fn:
                final_results[plan_name]["metrics"][metric_name] = {
                    "score": None,
                    "failed_cases": evaluable_cases,
                    "successful_cases": 0,
                    "note": "No strategy function mapped."
                }
                logger.warning(f"[{metric_name}] => No strategy function mapped.")
                print(f"[{metric_name}] => Score: None, Failed Cases: {evaluable_cases}, Successful Cases: 0")
                continue

            try:
                fn_name = strategy_fn.__name__
                logger.info(f"Evaluating [{metric_name}] using strategy: {fn_name}")

                if fn_name == "language_coverage":
                    score_list = await strategy_fn(collected_prompts, collected_responses)
                elif fn_name == "language_coverage_similarity":
                    score_list = await strategy_fn(collected_prompts, collected_responses, expected_outputs)
                elif fn_name in ["grammarcheck", "lexical_diversity"]:
                    score_list = await strategy_fn(collected_responses)
                elif fn_name == "llm_as_judge":
                    score_list = []
                    for i in range(len(collected_prompts)):
                        scores = strategy_fn(
                            metric_name=metric_name,
                            #task_intro="Evaluate the LLM response",
                            judge_prompt="Check if the response aligns with expectations",
                            system_prompt=sys_prompts[i],
                            prompts=[collected_prompts[i]],
                            test_case_response=[collected_responses[i]],
                            expected_response=[expected_outputs[i]]
                        )
                        score_list.extend(scores)
                elif fn_name == "text_similarity":
                    score_list = strategy_fn(collected_prompts, collected_responses, expected_outputs)
                elif fn_name == "toxicity_model_result":
                    score_list = strategy_fn(collected_responses)
                elif fn_name == "bleu_score_metric":
                    score_list = strategy_fn(collected_responses, expected_outputs)
                elif fn_name == "meteor_metric":
                    score_list = strategy_fn(collected_prompts, collected_responses)
                elif fn_name == "rouge_score_metric":
                    rouge_result = strategy_fn(collected_prompts, collected_responses)
                    score_list = [rouge_result.get("rouge1", 0)] * len(collected_prompts)
                else:
                    raise ValueError(f"Unknown strategy function: {fn_name}")

                if not score_list:
                    raise ValueError("No scores returned from strategy")

                PASS_THRESHOLD = 0.6
                successful_cases = sum(1 for score in score_list if score >= PASS_THRESHOLD)
                failed_cases = evaluable_cases - successful_cases
                avg_score = round(sum(score_list) / len(score_list), 3)

            except Exception as e:
                logger.error(f"[{metric_name}] Error: {str(e)}")
                avg_score = None
                successful_cases = 0
                failed_cases = evaluable_cases

            final_results[plan_name]["metrics"][metric_name] = {
                "score": avg_score,
                "failed_cases": failed_cases,
                "successful_cases": successful_cases
            }

            logger.info(f"[{metric_name}] => Score: {avg_score}, Failed: {failed_cases}, Passed: {successful_cases}")
            print(f"[{metric_name}] => Score: {avg_score}, Failed Cases: {failed_cases}, Successful Cases: {successful_cases}")

asyncio.run(analyze())

output_path = "../../Data/response_analysis_output.json"
with open(output_path, "w", encoding='utf-8') as f:
    json.dump(final_results, f, indent=2, ensure_ascii=False)

print(f"\nResults saved to: {output_path}")
logger.info(f"Results saved to: {output_path}")

# -----------------Tabulation ---------------------------------------------------------
MAX_WIDTH = 25
TSV_OUTPUT_PATH = "../../Data/evaluation_summary.tsv"

def wrap(text, width=MAX_WIDTH):
    return "\n".join(textwrap.wrap(str(text), width=width))

with open(output_path, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []
tsv_rows = []

for test_plan, plan_info in data.items():
    metrics = plan_info.get("metrics", {})
    metrics_list = list(metrics.items())

    for i, (metric, metric_info) in enumerate(metrics_list):
        score = metric_info.get("score")
        failed = metric_info.get("failed_cases", 0)
        passed = metric_info.get("successful_cases", 0)
        total_samples = passed + failed

        if score is None:
            score_str = f"{Fore.RED}N/A{Style.RESET_ALL}"
            score_plain = "N/A"
        else:
            color = Fore.GREEN if score >= 0.5 else Fore.RED
            score_str = f"{color}{score:.3f}{Style.RESET_ALL}"
            score_plain = f"{score:.3f}"

        summary = f"No. of test samples passed - {passed}\nNo. of test samples failed - {failed}"

        row = [
            wrap(test_plan) if i == 0 else "",
            wrap(metric),
            score_str,
            summary
        ]
        rows.append(row)

        tsv_rows.append([
            test_plan if i == 0 else "",
            metric,
            score_plain,
            f"Passed: {passed}, Failed: {failed}, Total: {total_samples}"
        ])
    rows.append(["-" * MAX_WIDTH] * 4)

headers = ["TEST PLAN", "METRICS", "SCORE", "SUMMARY"]
print(tabulate(rows, headers=headers, tablefmt="fancy_grid", colalign=("center", "center", "center", "left")))

tsv_headers = ["TEST PLAN", "METRICS", "SCORE", "SUMMARY"]
with open(TSV_OUTPUT_PATH, "w", newline='', encoding='utf-8') as tsvfile:
    writer = csv.writer(tsvfile, delimiter="\t")
    writer.writerow(tsv_headers)
    writer.writerows(tsv_rows)

print(f"\nTSV file saved at: {TSV_OUTPUT_PATH}")
