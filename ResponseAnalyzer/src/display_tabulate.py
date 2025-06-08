import json
import textwrap
import csv
from tabulate import tabulate
from colorama import Fore, Style, init
init(autoreset=True)
MAX_WIDTH = 25
TSV_OUTPUT_PATH = "data/evaluation_summary.tsv"
def wrap(text, width=MAX_WIDTH):
    return "\n".join(textwrap.wrap(str(text), width=width))
with open("data/response_analysis_output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []
tsv_rows = []

for test_plan, plan_info in data.items():
    metrics = plan_info["metrics"]
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
