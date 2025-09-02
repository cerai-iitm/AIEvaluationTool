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

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to 

from lib.orm.DB import DB
from lib.utils import get_logger, get_logger_verbosity

def main():
    # setup up logging
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Response Analysis Report Generator")
    parser.add_argument("--config", dest='config', default="config.json", help="Path to the config file")
    parser.add_argument("--get-config-template", "-T", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
    parser.add_argument("--get-runs", "-N", dest="get_runs", action="store_true", help="Get all test runs")
    parser.add_argument("--run-name", "-r", dest="run_name", type=str, help="Name of the run to evaluate")
    parser.add_argument("--force", "-f", dest="force", default=False, action="store_true", help="Force evaluation of already evaluated runs")

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
    if args.config:
        if not os.path.exists(args.config):
            logger.error(f"Configuration file '{args.config}' does not exist.")
            return
        with open(args.config, 'r') as config_file:
            try:
                config = json.load(config_file)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing configuration file: {e}")
                return
    else:
        logger.error("No configuration file provided.")
        return
    
    # setting up the database connection
    db_url = f"mariadb+mariadbconnector://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
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
        score_card[detail.plan_name][detail.metric_name]["Testcases"][detail.testcase_name] = conversation.evaluation_score

    table = Table(title=f"Response Analysis Report for Run '{run.run_name}'")
    table.add_column("Plan Name", style="cyan", no_wrap=True)
    table.add_column("Metric Name", style="magenta")
    table.add_column("Score (0-1)", style="green")
    
    # iterate through the dictionary to create score summaries.
    for plan in score_card.keys():
        for metric in score_card[plan].keys():
            scores = list(score_card[plan][metric]["Testcases"].values())
            avg_score = None
            if scores:
                avg_score = round(sum(scores) / len(scores), 2)
                
            score_card[plan][metric]["Average"] = avg_score
            table.add_row(plan, metric, str(avg_score) if avg_score != None else "N/A")

    print(json.dumps(score_card, indent=4))
    Console().print(table)

if __name__ == "__main__":
    main()