# @author Sudarsun Santhiappan
# @date 2025-08-21
# @updated 2025-08-21
# @description This module provides functionality for analyzing responses received from the target AI agent under test.

from datetime import datetime
import sys, os
import argparse
import json
from typing import List

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to 

from lib.orm.DB import DB
from lib.utils import get_logger, get_logger_verbosity
# from lib.strategy.strategy_implementor import StrategyImplementor
from lib.strategy.strategy_implementor import StrategyImplementor

def main():
    # setup up logging
    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Response Analyzer")
    parser.add_argument("--config", dest='config', default="config.json", help="Path to the config file")
    parser.add_argument("--get-config-template", "-T", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
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
    
    print(run_details)
    # let's group the all the run_details by strategy for computational convenience.
    grouped_run_details = {}
    for detail in run_details:
        # fetch the strategy name assigned for the testcase
        strategy_name = db.get_testcase_strategy_name(testcase_name=detail.testcase_name)
        if not strategy_name:
            logger.error(f"Strategy not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
            continue

        group_key = strategy_name + ":" + detail.metric_name
        if group_key not in grouped_run_details:
            grouped_run_details[group_key] = []
        grouped_run_details[group_key].append(detail)

    # brought it out from the for loop below since strategyimplementor should not have to be initialized for every strategy
    strategy = StrategyImplementor()

    for group in grouped_run_details.keys():
        strategy_name, metric_name = group.split(":")

        # instead of initializing the strategyimplementor for every strategy, we just set its name and the metric name
        strategy.set_metric_strategy(strategy_name=strategy_name, metric_name=metric_name)
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

            # check if the testcase prompt is consistent
            if not testcase.prompt:
                logger.error(f"Prompt not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
                continue
            if not testcase.prompt.user_prompt:
                logger.error(f"User prompt not found for testcase '{detail.testcase_name}' in run '{run.run_name}'.")
                continue

            # check if the conversation object is consistent
            conversation = db.get_conversation_by_id(detail.conversation_id)
            if not conversation:
                logger.error(f"Conversation with ID '{detail.conversation_id}' not found for run '{run.run_name}'.")
                continue
            if conversation.evaluation_ts:
                # if conversation has already been evaluated and not forced, skip re-evaluation
                if not args.force:
                    logger.warning(f"Conversation with ID '{detail.conversation_id}' in run '{run.run_name}' has already been evaluated on {conversation.evaluation_ts}. Skipping re-evaluation.")
                    continue
                # we will be re-evaluating the conversation
                logger.debug(f"Force re-evaluating conversation with ID '{detail.conversation_id}' in run '{run.run_name}'.")
            if not conversation.agent_response:
                logger.error(f"Agent response not found for conversation ID '{detail.conversation_id}' in run '{run.run_name}'.")
                continue
            
            """
            just need to change here, pass conversation and testcase objects
            """
            
            logger.debug(f"Evaluating strategy '{strategy_name}' for Testcase '{detail.testcase_name}'")
            # changed this line
            score = strategy.execute(testcase = testcase, conversation = conversation)
            # score = strategy.execute(prompts=[testcase.prompt.user_prompt], 
            #                          expected_responses=[testcase.response.response_text] if testcase.response else [None],
            #                          agent_responses=[conversation.agent_response], 
            #                          system_prompts=[testcase.prompt.system_prompt] if testcase.prompt.system_prompt else [None],
            #                          judge_prompts=[testcase.judge_prompt.prompt] if testcase.judge_prompt else [None])

            logger.debug(f"Evaluated score for conversation ID {conversation.conversation_id} in run '{run.run_name}' and Testcase '{detail.testcase_name}': {score}")
            # now, let's update the scores for each conversation
            conversation.evaluation_score = score
            conversation.evaluation_reason = ""
            conversation.evaluation_ts = datetime.now().isoformat()

            # record the evaluation details
            logger.debug(f"Recording evaluation score '{conversation.evaluation_score}' for Testcase '{detail.testcase_name}', conversation ID {conversation.conversation_id} in run '{run.run_name}'")
            db.add_or_update_conversation(conversation=conversation, override=args.force)

if __name__ == "__main__":
    main()

