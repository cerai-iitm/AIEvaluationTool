# @author Sudarsun
# @date 2025-08-28
# @description This module provides functionality for generating reports based on response analysis for a given test run.

from datetime import datetime
import sys, os
import argparse
import json
from typing import List
from rich.console import Console
from rich.table import Table
from pathlib import Path

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to 

from lib.orm.DB import DB
from lib.utils import get_logger, get_logger_verbosity
from lib.strategy.utils_new import OllamaConnect
from lib.strategy.utils_new import EvaluationReport

def main():
    # setup up logging
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Response Analysis Report Generator")
    parser.add_argument("--config", "-c", dest='config', default="config.json", help="Path to the config file")
    parser.add_argument("--get-config-template", "-T", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
    parser.add_argument("--get-runs", "-N", dest="get_runs", action="store_true", help="Get all test runs")
    parser.add_argument("--run-name", "-r", dest="run_name", type=str, help="Name of the run to evaluate")
    parser.add_argument("--force", "-f", dest="force", default=False, action="store_true", help="Force evaluation of already evaluated runs")
    parser.add_argument("--get-report", "-R", dest="get_report", action="store_true", help="Flag to generate PDF report after evaluation")

    args = parser.parse_args()

    # set the loglevel based on the verbosity argument.
    loglevel = get_logger_verbosity(args.verbosity)
    logger.setLevel(loglevel)

    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "user name",
            "password": "password*",
            "database": "db name",
        }
    }

    logger.info("Starting the AI Agent Response Analysis Report Generator...")

    # generate the configuration file template if requested
    if args.get_config_template:
        logger.info("Printing the configuration file template")
        print(json.dumps(config, indent=4))
        return
    
    # Load configuration from the specified file if provided
    BASE_DIR = Path(__file__).resolve().parents[3]
    config_path = BASE_DIR / args.config
    if args.config:
        if not os.path.exists(config_path):
            logger.error(f"Configuration file '{args.config}' does not exist.")
            return
        with open(config_path, 'r') as config_file:
            try:
                config = json.load(config_file)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing configuration file: {e}")
                return
    else:
        logger.error("No configuration file provided.")
        return
    
    # setting up the database connection
    # db_url = f"mariadb+mariadbconnector://{config["db"]['user']}:{config["db"]['password']}@{config["db"]['host']}:{config["db"]['port']}/{config["db"]['database']}"

    # set the default value of project root to current directory, we will adjust it based on the location of this file.
    project_root = "./"

    # setting up the database connection
    if config["db"]["engine"] == "sqlite":
        db_file = config["db"].get("file", "app.db")

        # Resolve project root (this file → importer → app → src → project_root)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

        # Place DB inside project_root/data
        db_folder = os.path.join(project_root, "data")
        os.makedirs(db_folder, exist_ok=True)

        # Full DB path
        db_path = os.path.join(db_folder, db_file)

        # SQLite requires a file URL
        db_url = f"sqlite:///{db_path}"

    else:
        # Original MariaDB path (fallback)
        db_url = (
            f"mariadb+mariadbconnector://"
            f"{config['db']['user']}:{config['db']['password']}"
            f"@{config['db']['host']}:{config['db']['port']}/"
            f"{config['db']['database']}"
        )

    try:
        logger.info(f"Database URL: {db_url}")
        db = DB(db_url=db_url, debug=False, loglevel=loglevel)
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        return
    
    # Logic to get all test runs
    if args.get_runs:
        # Create a table to display the test runs
        table = Table(title="Test Runs")
        table.add_column("Run ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        # Fetch all test runs from the database
        for run in db.runs:
            table.add_row(str(run.run_id), run.run_name, run.status)
        # Print the table of test runs
        Console().print(table)
        return

    # get the run information from the db.
    run = db.get_run_by_name(run_name=args.run_name)
    if not run:
        logger.error(f"Run with name '{args.run_name}' not found.")
        return
    
    # we don't want to deal with incomplete runs.
    #@NOTE we may have a force option, a little later, to evaluate an incomplete run.
    if run.status != "COMPLETED":
        logger.error(f"Run '{args.run_name}' is not completed. Current status: {run.status}")
        return

    run_details = db.get_all_run_details_by_run_name(run_name=run.run_name)
    if not run_details:
        logger.error(f"No run details found for run '{args.run_name}'.")
        return
    
    # collect the scores from the db to create a dictionary
    score_card = {}
    for detail in run_details:
        conversation = db.get_conversation_by_id(conversation_id=detail.conversation_id)
        if not conversation:
            logger.warning(f"Conversation with ID '{detail.conversation_id}' not found in run '{run.run_name}'.")
            continue
        if not conversation.evaluation_ts or conversation.evaluation_score == None:
            logger.warning(f"Conversation with ID '{detail.conversation_id}' in run '{run.run_name}' has not been evaluated yet. Skipping.")
            continue
        
        if detail.plan_name not in score_card:
            score_card[detail.plan_name] = {}

        if detail.metric_name not in score_card[detail.plan_name]:
            score_card[detail.plan_name][detail.metric_name] = {"Testcases":{}}

        # capture the score computed for the testcase.
        score_card[detail.plan_name][detail.metric_name]["Testcases"][
            detail.testcase_name
        ] = conversation.evaluation_score

        score_card[detail.plan_name][detail.metric_name].setdefault(
            "Evaluation_Reason", {}
        )[detail.testcase_name] = conversation.evaluation_reason

    # ------------------------------------------------------------
    # Determine plan context
    # ------------------------------------------------------------
    real_plans = [p for p in score_card if p != "PlanSummary"]
    multi_plan = len(real_plans) > 1


    # ------------------------------------------------------------
    # FIRST PASS: Metric-level summaries
    # ------------------------------------------------------------
    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        for metric_name, metric_data in metrics.items():

            scores = list(metric_data.get("Testcases", {}).values())
            reasons = list(metric_data.get("Evaluation_Reason", {}).values())

            if not scores:
                continue

            metric_score = round(sum(scores) / len(scores), 3)

            metric_summary = OllamaConnect.get_metric_summary(
                metric_name,
                scores=scores,
                reasons=reasons
            )

            metric_data.update({
                "metric_summary": metric_summary,
                "metric_score": metric_score
            })


    # ------------------------------------------------------------
    # SECOND PASS: Plan-level summaries
    # ------------------------------------------------------------

    # initialize the plan_summary for each plan, we will update it in place in the score_card
    plan_summary = ""
    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        plan_summary = OllamaConnect.get_single_plan_summary(plan_name, metrics)

        for metric_data in metrics.values():
            metric_data["plan_summary"] = plan_summary


    # ------------------------------------------------------------
    # THIRD PASS: Run-level summary (after plans exist)
    # ------------------------------------------------------------
    run_summary = OllamaConnect.get_run_summary(score_card) if multi_plan else ""

    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        for metric_data in metrics.values():
            metric_data["run_summary"] = run_summary


    # ------------------------------------------------------------
    # TABLE RENDERING
    # ------------------------------------------------------------
    table = Table(title=f"Response Analysis Report for Run '{run.run_name}'")
    table.add_column("Plan Name", style="cyan", no_wrap=True)
    table.add_column("Metric Name", style="magenta")
    table.add_column("Score (0-1)", style="green")
    table.add_column("Metric Summary", style="blue")
    table.add_column("Plan Summary", style="yellow")

    if multi_plan:
        table.add_column("Run Summary", style="blue")

    run_written = False

    for plan_name, metrics in score_card.items():
        if plan_name == "PlanSummary":
            continue

        plan_written = False

        for metric_name, metric_data in metrics.items():

            if "metric_summary" not in metric_data:
                continue

            row = [
                plan_name,
                metric_name,
                str(metric_data["metric_score"]),
                metric_data["metric_summary"],
                metric_data["plan_summary"] if not plan_written else ""
            ]

            if multi_plan:
                row.append(metric_data["run_summary"] if not run_written else "")

            table.add_row(*row)

            plan_written = True
            run_written = True


    print(json.dumps(score_card, indent=4))
    Console().print(table)

    reports_folder = os.path.join(project_root, "reports")
    os.makedirs(reports_folder, exist_ok=True)

    run = db.get_run_by_name(run_name=args.run_name)
    if not run:
        logger.error(f"Run with name '{args.run_name}' not found.")
        return
    
    target_name = getattr(run, "target")
    run_name = getattr(run, "run_name")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Also save the scrore_card as a JSON for reference.
    json_path = os.path.join(reports_folder, f"AI_Evaluation_Report_{target_name}_{run_name}.json")
    with open(json_path, "w") as json_file:
        json.dump(score_card, json_file, indent=4)

    total_testcases = sum(
        len(m.get("Testcases", {}))
        for metrics in score_card.values()
        for m in metrics.values()
    )

    if not args.get_report:
        logger.info("Report generation skipped as per the argument. Use --get-report or -R flag to generate the PDF report.")
        return

    # ------------------------------------------------------------
    # PDF generation
    # ------------------------------------------------------------

    report_generator = EvaluationReport()
    headers, rows = report_generator.scorecard_to_table(score_card)
    output_file = os.path.join(
        reports_folder,
        f"AI_Evaluation_Report_{target_name}_{run_name}.pdf"
    )
    filename = report_generator.create_report(
        target_name=target_name,
        run_name=run_name,
        timestamp=timestamp,
        total_testcases=total_testcases,
        run_summary=run_summary,
        headers=headers,
        rows=rows,
        score_card=score_card,
        output_file=output_file,
    )

    logger.info(
        f"PDF Report generated for target: '{target_name}', "
        f"run: '{run_name}', timestamp: '{timestamp}' "
        f"with total test cases: {total_testcases}"
    )

    logger.info(f"Report saved to: {filename}")
    
if __name__ == "__main__":
    main()

    