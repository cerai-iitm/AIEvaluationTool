# @author: Sudarsun S
# @date: 2025-07-10
# @description: This script serves as the main entry point for executing test cases in the AI Evaluation Tool.
# It handles command-line arguments for configuration, fetching test plans, and executing test cases
# using the InterfaceManagerClient from the lib directory.

import argparse
import sys
import os
import json
import logging
from rich.console import Console
from rich.table import Table

sys.path.append(os.path.dirname(__file__) + "/../../")  # Adjust the path to include the "lib" directory

from lib.interface_manager import InterfaceManagerClient  # Import the InterfaceManagerClient from the lib directory
from lib.orm import DB  # Import the DB class from the ORM module

def main():
    """ Main function to handle command-line arguments and execute test cases.
    This function initializes the argument parser, processes the command-line arguments,
    and sets up the configuration for the InterfaceManagerClient.
    It also provides options to get a configuration template, fetch test plans, and execute specific test cases.
    """

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch_formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)7s|%(funcName)s|%(message)s") # 
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    logger.info("Starting the Testcase Executor...")

    # Set up the argument parser
    ##############################################################################
    # This section defines the command-line arguments that can be passed to the script.
    # The arguments include options for configuration file, fetching test plans,
    # executing specific test cases, and setting a maximum number of test cases to execute.
    # The parser also includes flags to get a configuration template and to fetch all test plans.
    #
    # Example usage:
    # python main.py --get-config-template
    # python main.py --config-file config.json --get-plans
    # python main.py --config-file config.json --test-plan-id 1 --testcase-id 2 --max-testcases 5
    ##############################################################################
    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Testcase Executor")
    parser.add_argument("--config-file", dest="config", type=str, help="Path to the configuration file containing database connection and target application details.")
    parser.add_argument("--get-config-template", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--get-plans", dest="get_plans", action="store_true", help="Flag to get all test plans")
    parser.add_argument("--get-testcases", dest="get_testcases", action="store_true", help="Flag to get all test cases for a specific test plan")
    parser.add_argument("--test-plan-id", dest="plan_id", type=int, help="ID of the test plan to execute")
    parser.add_argument("--testcase-id", dest="testcase_id", type=int, help="ID of the specific test case to execute")
    parser.add_argument("--max-testcases", dest="max_testcases", type=int, default=10, help="Maximum number of test cases to execute (default: 10)")
    
    args = parser.parse_args()

    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "user name",
            "password": "password*",
            "database": "db name",
        },
        "target": {
            "application_type": "WHATSAPP-WEB | WEBAPP",
            "application_name": "Name of the target application",
            "application_url": "http://localhost:8000",  # URL of the target application
            "agent_name": "Name of the AI agent",
        }
    }

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
    
    db_url = f"mariadb+mariadbconnector://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['database']}"
    try:
        logger.info(f"Database URL: {db_url}")
        db = DB(db_url=db_url, debug=False)
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        return
    
    if args.get_plans:
        # Logic to get all test plans
        logger.info("Fetching all test plans...")

        # Create a table to display the test plans
        table = Table(title="Test Plans")
        table.add_column("Plan ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")
        # Fetch all test plans from the database
        for plan in db.plans:
            table.add_row(str(plan.plan_id), plan.plan_name, plan.plan_description)
        # Print the table of test plans
        Console().print(table)
        return
    
    # Get all test cases, optionally for a specific test plan if stated.
    if args.get_testcases:
        # Logic to get all test cases for a specific test plan
        if args.plan_id is None:
            logger.info("Test plan ID not provided, pulling the names of all test cases")
            table = Table(title="Test Cases")
            table.add_column("Test Case ID", justify="right", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Strategy", style="green")
            # Fetch all test cases from the database
            for tc in db.testcases:
                table.add_row(str(tc.testcase_id), tc.name, tc.strategy)
            # Print the table of test cases
            Console().print(table)
            return
        
        plan_name = db.get_testplan_name(plan_id=args.plan_id)
        if plan_name is None:
            logger.error(f"No test plan found with ID {args.plan_id}.")
            return
        # Log the plan name and ID
        logger.info(f"Fetching test cases for plan: {plan_name} ({args.plan_id})")
        
        # Create a table to display the test cases
        table = Table(title=f"Test Cases for Plan ID {args.plan_id}")
        table.add_column("Test Case ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Strategy", style="green")
        
        # Fetch test cases for the specified plan ID
        testcases = db.get_testcases_by_testplan(plan_name=plan_name, n=args.max_testcases)
        for testcase in testcases:
            table.add_row(str(testcase.testcase_id), testcase.name, testcase.strategy)
        
        # Print the table of test cases
        Console().print(table)
        return


    # Initialize the InterfaceManagerClient with the provided configuration
    client = InterfaceManagerClient(base_url="http://localhost:8000", application_type="")


if __name__ == "__main__":
    main()

    