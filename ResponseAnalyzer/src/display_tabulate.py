import json
import textwrap
from tabulate import tabulate
from colorama import Fore, Style, init

init(autoreset=True)

MAX_WIDTH = 25
TOTAL_SAMPLES_PER_METRIC = 3  # Adjust if needed

def wrap(text, width=MAX_WIDTH):
    return "\n".join(textwrap.wrap(str(text), width=width))

with open("data/response_analysis_output.json", "r") as f:
    data = json.load(f)

rows = []
for test_plan, plan_info in data.items():
    metrics = plan_info["metrics"]
    metrics_list = list(metrics.items())

    for i, (metric, metric_info) in enumerate(metrics_list):
        score = metric_info["score"]
        failed = metric_info["failed_cases"]
        passed = TOTAL_SAMPLES_PER_METRIC - failed

        if score is None:
            score_str = f"{Fore.RED}N/A{Style.RESET_ALL}"
        else:
            color = Fore.GREEN if score >= 0.5 else Fore.RED
            score_str = f"{color}{score:.3f}{Style.RESET_ALL}"

        summary = f"No. of test samples passed - {passed}\n No. of test samples failed - {failed}"

        row = [
            wrap(test_plan) if i == 0 else "",
            wrap(metric),
            score_str,
            summary
        ]
        rows.append(row)

    rows.append(["-" * MAX_WIDTH] * 4)

headers = ["TEST PLAN", "METRICS", "SCORE", "SUMMARY"]

print(tabulate(rows, headers=headers, tablefmt="fancy_grid", colalign=("center", "center", "center", "left")))