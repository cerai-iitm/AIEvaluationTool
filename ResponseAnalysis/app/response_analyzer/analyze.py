# @author Sudarsun Santhiappan
# @date 2025-08-21
# @updated 2025-08-21
# @description This module provides functionality for analyzing responses received from the target AI agent under test.

import sys, os
import argparse
import json
from typing import List

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to 

from lib.orm.DB import DB
from lib.utils import get_logger, get_logger_verbosity
from lib.strategy.strategy_implementor import StrategyImplementor

def main():
    # setup up logging
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Response Analyzer")
    parser.add_argument("--config", dest='config', default="config.json", help="Path to the config file")
    parser.add_argument("--get-config-template", "-T", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
    parser.add_argument("--run-name", "-r", dest="run_name", type=str, help="Name of the run to evaluate")

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

    logger.info("Starting the AI Agent Response Analyzer...")

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
    
    # let's group the all the run_details by strategy for computational convenience.
    grouped_run_details = {}
    for detail in run_details:
        # fetch the strategy name assigned for the testcase
        strategy_name = db.get_testcase_strategy_name(testcase_name=detail.testcase_name)
        if not strategy_name:
            logger.error(f"Strategy not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
            continue

        if strategy_name not in grouped_run_details:
            grouped_run_details[strategy_name + ":" + detail.metric_name] = []
        grouped_run_details[strategy_name + ":" + detail.metric_name].append(detail)

    for group in grouped_run_details.keys():
        strategy_name, metric_name = group.split(":")

        prompts:List[str] = []
        system_prompts:List[str] = []
        judge_prompts:List[str] = []
        agent_responses:List[str] = []
        expected_responses:List[str] = []

        # Analyze the run details
        for detail in grouped_run_details[group]:
            # let's ignore the incomplete test cases.
            if detail.status != "COMPLETED":
                logger.warning(f"Skipping incomplete run detail with ID {detail.detail_id} for run '{run.run_name}'. Current status: {detail.status}")
                continue

            testcase = db.get_testcase_by_name(detail.testcase_name)
            if not testcase:
                logger.error(f"Testcase '{detail.testcase_name}' not found for run '{run.run_name}'.")
                continue

            conversation = db.get_conversation_by_id(detail.conversation_id)
            if not conversation:
                logger.error(f"Conversation with ID '{detail.conversation_id}' not found for run '{run.run_name}'.")
                continue

            prompts.append(testcase.prompt.user_prompt)
            system_prompts.append(testcase.prompt.system_prompt)
            judge_prompts.append(testcase.judge_prompt.prompt if testcase.judge_prompt else None)
            agent_responses.append(conversation.agent_response)
            expected_responses.append(testcase.response.response_text)

        strategy = StrategyImplementor(strategy_name=strategy_name, metric_name=metric_name)
        scores = strategy.execute(prompts=prompts, expected_responses=expected_responses,
                                  agent_responses=agent_responses, system_prompts=system_prompts,
                                  judge_prompts=judge_prompts)


if __name__ == "__main__":
    main()

