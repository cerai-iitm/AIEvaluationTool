# @author: Sudarsun S
# @date: 2025-07-10
# @updated: 2025-07-22
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
from datetime import datetime
import randomname  # Importing the randomname library for generating random names


#@NOTE To add domain specific testcase sampling.


sys.path.append(os.path.dirname(__file__) + "/../../")  # Adjust the path to include the "lib" directory

from lib.interface_manager import InterfaceManagerClient  # Import the InterfaceManagerClient from the lib directory
from lib.orm import DB  # Import the DB class from the ORM module
from lib.data import Target, Run, RunDetail, Conversation
from lib.utils import get_logger, get_logger_verbosity

def main():
    """ Main function to handle command-line arguments and execute test cases.
    This function initializes the argument parser, processes the command-line arguments,
    and sets up the configuration for the InterfaceManagerClient.
    It also provides options to get a configuration template, fetch test plans, and execute specific test cases.
    """

    # Set up logging
    logger = get_logger(__name__)

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
    parser = argparse.ArgumentParser(description="AI Evaluation Tool :: Test Executor")
    parser.add_argument("--config", "-c", dest="config", type=str, help="Path to the configuration file containing database connection and target application details.")
    parser.add_argument("--get-config-template", "-T", dest="get_config_template", action="store_true", help="Flag to get the configuration file template")
    parser.add_argument("--get-plans", "-P", dest="get_plans", action="store_true", help="Get all test plans")
    parser.add_argument("--get-metrics", "-M", dest="get_metrics", action="store_true", help="Get all the evaluation metrics")
    parser.add_argument("--get-testcases", "-C", dest="get_testcases", action="store_true", help="Get the test cases for a specific test plan or all test cases if no plan ID is provided")
    parser.add_argument("--get-targets", "-G", dest="get_targets", action="store_true", help="Get all target applications")
    parser.add_argument("--testplan-id", "-p", dest="plan_id", type=int, help="ID of the test plan to execute")
    parser.add_argument("--testcase-id", "-t", dest="testcase_id", type=int, help="ID of the specific test case to execute")
    parser.add_argument("--metric-id", "-m", dest="metric_id", type=int, help="ID of the evaluation metric to use")
    parser.add_argument("--max-testcases", "-n", dest="max_testcases", type=int, default=10, help="Maximum number of test cases to execute (default: 10)")
    parser.add_argument("--run-name", "-r", dest="run_name", type=str, help="Run name for the test plan or test case execution")
    parser.add_argument("--run-continue", "-R", dest="run_continue", default=False, action="store_true", help="Continue an existing run with the provided run name")
    parser.add_argument("--execute", "-e", dest="execute", action="store_true", help="Execute the test plan or test case")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, choices=[0,1,2,3,4,5], help="Enable verbose output", default=5)
    parser.add_argument("--get-runs", "-N", dest="get_runs", action="store_true", help="Get all test runs")

    args = parser.parse_args()

    # Set the logging level based on the verbosity argument
    loglevel = get_logger_verbosity(args.verbosity)
    logger.setLevel(loglevel)

    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "user name",
            "password": "password*",
            "database": "db name",
        },
        "target": {
            "application_type": "WHATSAPP_WEB | WEBAPP",
            "application_name": "Name of the target application",
            "application_url": "http://localhost:8000",  # URL of the target application
            "agent_name": "Name of the AI agent",
        }
    }

    logger.info("Starting the Testcase Executor...")

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

    # list all the known target applications
    if args.get_targets:
        # Logic to get all target applications
        logger.info("Fetching all target applications...")
        
        # Create a table to display the target applications
        table = Table(title="Target Applications")
        table.add_column("Target ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Domain", style="yellow")
        table.add_column("URL", style="blue")
        
        # Fetch all targets from the database
        for target in db.targets:
            table.add_row(str(target.target_id), target.target_name, target.target_type, target.target_domain, target.target_url)
        
        # Print the table of targets
        Console().print(table)
        return
    
    # setting up the Target Application
    if "application_name" not in config["target"]:
        logger.error("Application name not found in the configuration file.")
        return

    application_name = config["target"]["application_name"]
    application_type = config["target"]["application_type"]

    if "application_url" not in config["target"]:
        logger.error("Application URL not found in the configuration file.")
        return
    
    application_url = config["target"]["application_url"]

    if "agent_name" not in config["target"]:
        logger.error("Agent name not found in the configuration file.")
        return
    
    agent_name = config["target"]["agent_name"]

    target_id = db.get_target_id(target_name=application_name)
    if target_id is None:
        logger.error(f"Target application '{application_name}' not found in the database.")
        return
    
    target = db.get_target_by_id(target_id=target_id)
    if target is None:
        logger.error(f"Target application with ID {target_id} not found in the database.")
        return
    else:
        logger.info(f"Target application found: {target.target_name} (ID: {target.target_id})")
    
    # get the test plans
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
        table = Table(title=f"Test Cases for \"{plan_name}\" (PlanID:{args.plan_id})")
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

    # Get all evaluation metrics
    if args.get_metrics:
        # Logic to get all evaluation metrics
        logger.info("Fetching all evaluation metrics...")

        # Create a table to display the evaluation metrics
        table = Table(title="Evaluation Metrics")
        table.add_column("Metric ID", justify="right", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Description", style="green")
        
        # Fetch all metrics from the database
        for metric in db.metrics:
            table.add_row(str(metric.metric_id), metric.metric_name, metric.metric_description)
        
        # Print the table of evaluation metrics
        Console().print(table)
        return

    if args.execute:
        # Logic to execute the test case or test plan
        if args.plan_id is None and args.testcase_id is None:
            logger.error("Either test plan ID or test case ID must be provided for execution.")
            return
        
        # handle the "run" by creating a new run entry in the database or
        # using an existing "incomplete run" if the run name is provided
        if args.run_name is None:
            # generate a random run name if not provided
            run_name = randomname.generate('v/*','adj/*','n/*','ip/*')
            logger.debug(f"Run name not provided, creating a new Run \"{run_name}\"")
            # Create a new run entry in the database
            start_time = datetime.now().isoformat()
            run = Run(target = target.target_name, run_name=run_name, start_ts=start_time)
            run_id = db.add_or_update_testrun(run=run)
            logger.debug(f"Created new run with ID {run_id} and name '{run_name}'")
        else:
            run_name = args.run_name
            run = db.get_run_by_name(run_name=args.run_name)
            if run is None or run.status is None:
                if args.run_continue:
                    logger.debug(f"Run name '{args.run_name}' is not found, creating a new run...")
                    # Create a new run entry in the database
                    start_time = datetime.now().isoformat()
                    run = Run(target = target.target_name, run_name=run_name, start_ts=start_time)
                    run_id = db.add_or_update_testrun(run=run)
                    logger.debug(f"Created new run with ID {run_id} and name '{run_name}'")
                else:
                    logger.error(f"No run found with name '{args.run_name}'.  If you want to create a new one, pass '--run-continue' to the cmdline args.")
                    return
            else:
                if run.status == "COMPLETED":
                    if args.run_continue:
                        run.end_ts = None  # Reset the end timestamp to allow continuation
                        run.status = "RUNNING"
                        db.add_or_update_testrun(run=run, override=True)
                        logger.debug(f"Reopening the COMPLETED run with ID {run.run_id} and name '{run.run_name}'")
                    else:
                        logger.error(f"Run '{args.run_name}' is already completed!")
                        return
                    
                logger.debug(f"Using existing run with ID {run.run_id} and name '{run.run_name} with status '{run.status}'")
        
        # Fetch the test plan name
        if args.plan_id:
            plan_name = db.get_testplan_name(plan_id=args.plan_id)
            if plan_name is None:
                logger.error(f"No test plan found with ID {args.plan_id}.")
                return
            
            # if the testcase is is provided, we will execute the specific test case and skip the test plan execution.
            if args.testcase_id:
                # If a specific test case ID is provided, fetch the test case details
                testcase = db.get_testcase_by_id(testcase_id=args.testcase_id)
                if testcase is None:
                    logger.error(f"No test case found with ID {args.testcase_id}.")
                    return
                
                logger.debug(f"Executing test case: {testcase.name} (Case ID: {testcase.testcase_id}) from plan: {plan_name} (PlanID: {args.plan_id})")
                # Create a new run detail entry for the test case

                # if the run status is NEW, update the starting time.
                if run.status == "NEW":
                    run.start_ts = datetime.now().isoformat()
                    
                # change the run status to "RUNNING"
                run.status = "RUNNING"
                db.add_or_update_testrun(run=run)

                # create or update the run detail entry for the test case
                rundetail = RunDetail(run_name=args.run_name, plan_name=plan_name, metric_name=testcase.metric, testcase_name=testcase.name)
                rundetail_id = db.add_or_update_testrun_detail(rundetail)

                # fetch the run detail status.
                # if the run detail is already completed, skip the execution.
                run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                if run_status is not None and run_status == "COMPLETED":
                    logger.debug(f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution.")
                else:
                    logger.debug(f"Executing Test {testcase.name} (Case ID: {testcase.testcase_id})")

                    conv = Conversation(target=target.target_name, 
                                        run_detail_id=rundetail_id, 
                                        testcase=testcase.name)
                    # even if the conversation already exists, we will override it with the new information.
                    conv_id = db.add_or_update_conversation(conversation=conv, override=True)

                    # construct the message to send to the agent
                    message_to_agent = testcase.prompt.user_prompt if testcase.prompt.user_prompt else ""
                    if testcase.prompt.system_prompt:
                        message_to_agent = testcase.prompt.system_prompt + "\n" + message_to_agent

                    logger.debug(f"A new conversation is created with ID: {conv_id}")

                    rundetail.status = "RUNNING"
                    db.add_or_update_testrun_detail(rundetail)

                    # Initialize the InterfaceManagerClient with the provided configuration
                    client = InterfaceManagerClient(base_url=application_url, application_type=application_type)
                    client.sync_config({
                        "application_name": application_name,
                        "agent_name": agent_name,
                        "application_url": application_url
                    })

                    try:
                        conv.prompt_ts = datetime.now().isoformat()
                        db.add_or_update_conversation(conversation=conv)

                        response_from_agent = client.chat(chat_id = testcase.testcase_id, prompt_list=[message_to_agent])
                        agent_response = response_from_agent.json().get("response", "")

                        # Check if the response is empty or indicates a chat not found
                        # Here, we will leave the Conversation entry dangling in the DB to indicate the the conversation was not successful.
                        if len(agent_response) == 0 or agent_response[0]['response'] == "Chat not found":
                            logger.error(f"No response received from the agent for test case {testcase.testcase_id}.")
                            rundetail.status = "FAILED"
                            db.add_or_update_testrun_detail(rundetail)
                        else:
                            conv.response_ts = datetime.now().isoformat()
                            conv.agent_response = agent_response[0]['response']
                            db.add_or_update_conversation(conversation=conv)

                            rundetail.status = "COMPLETED"
                            db.add_or_update_testrun_detail(rundetail)

                            # Update the run status with the end timestamp
                            run.end_ts = datetime.now().isoformat()
                            run.status = "COMPLETED"
                            db.add_or_update_testrun(run=run)
                            logger.debug(f"Execution of test case '{testcase.name}' completed successfully.")

                    except Exception as e:
                        logger.error(f"Error during execution of test case {testcase.testcase_id}: {e}")
                        rundetail.status = "FAILED"
                        db.add_or_update_testrun_detail(rundetail)

                    finally:
                        try:
                            client.close()
                        except Exception as e:
                            logger.error(f"Error closing the client connection: {e}")

            # if the metric id is supplied, we will execute the testcases for the metric                            
            elif args.metric_id:
                # If a specific metric ID is provided, fetch the metric details
                metric_name = db.get_metric_name(metric_id=args.metric_id)
                if metric_name is None:
                    logger.error(f"No metric found with ID {args.metric_id}.")
                    return
                
                # get the test cases for the metric
                logger.debug(f"Fetching test cases for metric: {metric_name} (Plan: {plan_name}, Metric ID: {args.metric_id})")
                testcases = db.get_testcases_by_metric(metric_name=metric_name, n=args.max_testcases)
                if not testcases:
                    logger.error(f"No test cases found for metric: {metric_name} (Plan: {plan_name}, Metric ID: {args.metric_id})")
                    return
                               
                # If a specific metric ID is provided, fetch the metric details
                metric = db.get_metric_by_id(metric_id=args.metric_id)
                if metric is None:
                    logger.error(f"No metric found with ID {args.metric_id}.")
                    return
                
                logger.debug(f"Executing test cases for the metric: {metric.metric_name} (Plan: {plan_name}, Metric ID: {args.metric_id})")

                # if the run status is NEW, update the starting time.
                if run.status == "NEW":
                    run.start_ts = datetime.now().isoformat()
                    
                # change the run status to "RUNNING"
                run.status = "RUNNING"
                db.add_or_update_testrun(run=run)

                # Initialize the InterfaceManagerClient with the provided configuration
                client = InterfaceManagerClient(base_url=application_url, application_type=application_type)
                client.sync_config({
                    "application_name": application_name,
                    "agent_name": agent_name,
                    "application_url": application_url
                })

                # iterate through the test cases and execute
                for testcase in testcases:
                    # create a new run detail entry for each test case
                    rundetail = RunDetail(run_name=run_name, plan_name=plan_name, metric_name=testcase.metric, testcase_name=testcase.name)
                    rundetail_id = db.add_or_update_testrun_detail(rundetail)
                    
                    # fetch the run detail status.
                    # if the run detail is already completed, skip the execution.
                    run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                    if run_status is not None and run_status == "COMPLETED":
                        logger.debug(f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution.")
                        continue

                    logger.debug(f"Executing Test {testcase.name} (Case ID: {testcase.testcase_id})")

                    # construct the message to send to the agent
                    message_to_agent = testcase.prompt.user_prompt if testcase.prompt.user_prompt else ""
                    if testcase.prompt.system_prompt:
                        message_to_agent = testcase.prompt.system_prompt + "\n" + message_to_agent

                    conv = Conversation(target=target.target_name, 
                                        run_detail_id=rundetail_id, 
                                        testcase=testcase.name)
                    conv_id = db.add_or_update_conversation(conversation=conv)
                    logger.debug(f"A new conversation is created with ID: {conv_id}")

                    rundetail.status = "RUNNING"
                    db.add_or_update_testrun_detail(rundetail)

                    try:
                        conv.prompt_ts = datetime.now().isoformat()
                        db.add_or_update_conversation(conversation=conv)

                        response_from_agent = client.chat(chat_id = testcase.testcase_id, prompt_list=[message_to_agent])
                        agent_response = response_from_agent.json().get("response", "")

                        # Check if the response is empty or indicates a chat not found
                        # Here, we will leave the Conversation entry dangling in the DB to indicate the the conversation was not successful.
                        if len(agent_response) == 0 or agent_response[0]['response'] == "Chat not found":
                            logger.error(f"No response received from the agent for test case {testcase.testcase_id}.")
                            rundetail.status = "FAILED"
                            db.add_or_update_testrun_detail(rundetail)
                            continue

                        conv.response_ts = datetime.now().isoformat()
                        conv.agent_response = agent_response[0]['response']
                        db.add_or_update_conversation(conversation=conv)

                        rundetail.status = "COMPLETED"
                        db.add_or_update_testrun_detail(rundetail)

                    except Exception as e:
                        logger.error(f"Error during execution of test case {testcase.testcase_id}: {e}")
                        rundetail.status = "FAILED"
                        db.add_or_update_testrun_detail(rundetail)
                        continue

                try:
                    # close the client session.
                    client.close()
                except Exception as e:
                    logger.error(f"Error closing the client connection: {e}")

                # Update the run status to completed
                run.end_ts = datetime.now().isoformat()
                run.status = "COMPLETED"
                db.add_or_update_testrun(run=run)
                logger.debug(f"Execution of test plan '{plan_name}' completed successfully.")

            # execute the test plan if no specific test case is provided
            else:

                logger.debug(f"Executing test plan: {plan_name} (PlanID: {args.plan_id})")
                # fetch the test cases of the test plan
                testcases = db.get_testcases_by_testplan(plan_name=plan_name, n=args.max_testcases)
                if not testcases:
                    logger.error(f"No test cases found for plan: {plan_name} (PlanID: {args.plan_id})")
                    return
                
                # if the run status is NEW, update the starting time.
                if run.status == "NEW":
                    run.start_ts = datetime.now().isoformat()
                    
                # change the run status to "RUNNING"
                run.status = "RUNNING"
                db.add_or_update_testrun(run=run)

                # Initialize the InterfaceManagerClient with the provided configuration
                client = InterfaceManagerClient(base_url=application_url, application_type=application_type)
                client.sync_config({
                    "application_name": application_name,
                    "agent_name": agent_name,
                    "application_url": application_url
                })

                # iterate through the test cases and execute
                for testcase in testcases:
                    # create a new run detail entry for each test case
                    rundetail = RunDetail(run_name=run_name, plan_name=plan_name, metric_name=testcase.metric, testcase_name=testcase.name)
                    rundetail_id = db.add_or_update_testrun_detail(rundetail)
                    
                    # fetch the run detail status.
                    # if the run detail is already completed, skip the execution.
                    run_status = db.get_status_by_run_detail_id(run_detail_id=rundetail_id)
                    if run_status is not None and run_status == "COMPLETED":
                        logger.debug(f"Run detail for testcase {testcase.name} (ID: {testcase.testcase_id}) is already completed. Skipping execution.")
                        continue

                    logger.debug(f"Executing Test {testcase.name} (Case ID: {testcase.testcase_id})")

                    # construct the message to send to the agent
                    message_to_agent = testcase.prompt.user_prompt if testcase.prompt.user_prompt else ""
                    if testcase.prompt.system_prompt:
                        message_to_agent = testcase.prompt.system_prompt + "\n" + message_to_agent

                    conv = Conversation(target=target.target_name, 
                                        run_detail_id=rundetail_id, 
                                        testcase=testcase.name)
                    conv_id = db.add_or_update_conversation(conversation=conv)
                    logger.debug(f"A new conversation is created with ID: {conv_id}")

                    rundetail.status = "RUNNING"
                    db.add_or_update_testrun_detail(rundetail)

                    try:
                        conv.prompt_ts = datetime.now().isoformat()
                        db.add_or_update_conversation(conversation=conv)

                        response_from_agent = client.chat(chat_id = testcase.testcase_id, prompt_list=[message_to_agent])
                        agent_response = response_from_agent.json().get("response", "")

                        # Check if the response is empty or indicates a chat not found
                        # Here, we will leave the Conversation entry dangling in the DB to indicate the the conversation was not successful.
                        if len(agent_response) == 0 or agent_response[0]['response'] == "Chat not found":
                            logger.error(f"No response received from the agent for test case {testcase.testcase_id}.")
                            rundetail.status = "FAILED"
                            db.add_or_update_testrun_detail(rundetail)
                            continue

                        conv.response_ts = datetime.now().isoformat()
                        conv.agent_response = agent_response[0]['response']
                        db.add_or_update_conversation(conversation=conv)

                        rundetail.status = "COMPLETED"
                        db.add_or_update_testrun_detail(rundetail)

                    except Exception as e:
                        logger.error(f"Error during execution of test case {testcase.testcase_id}: {e}")
                        rundetail.status = "FAILED"
                        db.add_or_update_testrun_detail(rundetail)
                        continue

                try:
                    client.close()
                except Exception as e:
                    logger.error(f"Error closing the client connection: {e}")

                # Update the run status to completed
                run.end_ts = datetime.now().isoformat()
                run.status = "COMPLETED"
                db.add_or_update_testrun(run=run)
                logger.debug(f"Execution of test plan '{plan_name}' completed successfully.")

if __name__ == "__main__":
    main()

    