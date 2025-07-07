# TestExecutionManager.py

import json
import argparse
from typing import List, Dict, Union
import sys, os
import logging
from pathlib import Path
import random

sys.path.append(os.path.relpath("../.."))
from InterfaceManager import InterfaceManagerClient

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("send_prompts.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

current_file = Path(__file__).resolve()

# Setting path to the Data folder
plans_path = current_file.parents[2] / "Data" / "plans.json"

data_points_path = current_file.parents[2] / "Data" / "DataPoints.json"

response_file = current_file.parents[2] / "Data" / "responses.json"

parser = argparse.ArgumentParser(description="LLM Evaluation Suite - A comprehensive evaluation tool for verifying conversational AI applications.")

parser.add_argument("--base_url", type=str, default="http://localhost:8000", help="Base URL of the server (Default: 'http://localhost:8000')")
parser.add_argument("--application_type", type=str.upper, default="WHATSAPP_WEB", help="Application type: required for LLM evaluation (e.g., WHATSAPP_WEB or OPENUI)")
parser.add_argument("--agent_name", type=str, default="Gooey AI", help="Model name for the application (Default set to ChatGPT)")
parser.add_argument("--openui_email", type=str, help="OpenUI email: required for OpenUI Application")
parser.add_argument("--openui_password", type=str, help="OpenUI password: required for OpenUI Application")
parser.add_argument("--run_mode", default="single_window", type=str, help="How to handle prompt session", choices=["single_window", "multiple_window"])

# group = parser.add_mutually_exclusive_group(required=True)
# group.add_argument("--prompt", type= str, help="Send a single prompt to the conversational AI application")
# group.add_argument("--prompt_from_excel", type=str, default="sample.xlsx", help="Path to Excel file containing prompts")
# group.add_argument("--data", default="test.json", help="Default json file")

parser.add_argument(
    "--test_plan_id", 
    required=True, 
    help="""Specify the Test Plan ID:\n
  T1 - Responsible AI\n
  T2 - Conversational Quality\n
  T3 - Guardrails and Safety\n
  T4 - Language Support\n
  T5 - Task Understanding\n
  T6 - Business Requirements Alignment\n"""
    
)
#--test_case_count - instead of --n
parser.add_argument("--test_case_count", type=int, help="Number of Prompts to run in a Test Plan", default=2)
parser.add_argument("--action", type=str, help="Send all Prompts", default="send_all_prompts")
parser.add_argument("--test_plan_file", default=str(data_points_path), help="Default json file")

args = parser.parse_args()

# Dynamically set test_case_count to the total number of prompts in the selected test plan if not provided
if args.test_case_count is None:
    # Load plans and datapoints
    with open(plans_path, 'r', encoding='utf-8') as plan_file:
        all_plans = json.load(plan_file)
    plan_entry = all_plans.get(args.test_plan_id, {})
    metric_ids = list(plan_entry.get('metrics', {}).keys())
    with open(args.test_plan_file, 'r', encoding='utf-8') as case_file:
        all_cases_by_metric = json.load(case_file)
    total_prompts = 0
    for metric_id in metric_ids:
        metric_data = all_cases_by_metric.get(metric_id, {})
        cases = metric_data.get('cases', [])
        total_prompts += len(cases)
    args.test_case_count = total_prompts

# Validation based on application type
if args.application_type == "WHATSAPP_WEB":
    if not args.agent_name:
        parser.error("--agent_name is required when --application_type is 'WHATSAPP_WEB'")
elif args.application_type == "OPENUI":
    missing = []
    if not args.agent_name:
        missing.append("--agent_name")
    if not args.openui_email:
        missing.append("--openui_email")
    if not args.openui_password:
        missing.append("--openui_password")
    if missing:
        parser.error(f"Missing required arguments for 'OPENUI': {', '.join(missing)}")

class TestCaseExecutionManager:
    def __init__(self, test_plan_file, test_plan_id, limit=None, **client_args):
        self.test_plan_file = test_plan_file
        self.test_plan_id = test_plan_id
        self.limit = limit
        self.test_plan_name = ""
        self.test_cases = self.load_test_cases()
        self.chat_id_count= 0

        if client_args.get("base_url"):
            self.client = InterfaceManagerClient(**client_args)
            self.client.initialize()
            self.client.sync_config(vars(args))
        else:
            self.client = None


    def load_test_cases(self) -> List[Dict]:
        try:

            with open(plans_path, 'r', encoding='utf-8') as plan_file:
                all_plans = json.load(plan_file)
                
            if self.test_plan_id not in all_plans:
                raise ValueError(f"Test plan ID '{self.test_plan_id}' not found in plans.json.")
        
            plan_entry = all_plans[self.test_plan_id]
            self.test_plan_name = plan_entry.get("TestPlan_name", "Unknown Plan")
            metric_ids = plan_entry.get("metrics", [])
        
            with open(self.test_plan_file, 'r', encoding='utf-8') as case_file:
                all_cases_by_metric = json.load(case_file)

            all_cases = []
            for metric_id in metric_ids:
                metric_data = all_cases_by_metric.get(metric_id)
                if not metric_data:
                    continue
                cases = metric_data.get("cases", [])
                all_cases.extend(cases)

            return all_cases[:self.limit] if self.limit else all_cases

        except FileNotFoundError as e:
            raise RuntimeError(f"Required file not found: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON Decode Error: {e}")

    def assign_chat_id(self):
        chat_id = self.chat_id_count
        self.chat_id_count+= 1
        return chat_id

    def send(self, chat_id: int, prompt: str) -> Dict[str, Union[str, int]]:
        """
        Sends a single prompt to the client for the given chat_id.
        Returns a dictionary containing the chat_id, prompt, and response.
        """
        if not self.client:
            return {
                "prompt": prompt,
                "response": "(no client) prompt was: '{}'".format(prompt)
            }

        try:
            print([prompt])
            response = self.client.chat(chat_id=chat_id, prompt_list=[prompt])
            data = response.json()

            if isinstance(data, dict) and "response" in data:
                resp = data["response"]
                if isinstance(resp, list) and resp and isinstance(resp[0], dict):
                    response_text = resp[0].get("response", "")
                else:
                    response_text = str(resp)
            if isinstance(data, dict) and "response" in data:
                resp = data["response"]
                if isinstance(resp, list) and resp and isinstance(resp[0], dict):
                    response_text = resp[0].get("response", "")
                else:
                    response_text = str(resp)
            else:
                response_text = ""

            return {
                "prompt": prompt,
                "response": response_text
            }

        except Exception as e:
            return {
                "prompt": prompt,
                "response": "Error: {}".format(e)
            }

    def send_all_prompts(self):
        logger.info("=== START: send_prompts ===")
        logger.info(f"Plan ID: {self.test_plan_id}")
        logger.info(f"Test plan file: {self.test_plan_file}")
        logger.info(f"Test case count: {self.limit}")

        results = []
        prompt_list = []
        prompt_id_list = []
        sent_prompts = set()

        with open(plans_path, 'r', encoding='utf-8') as plan_file:
            all_plans = json.load(plan_file)
            plan_entry = all_plans[self.test_plan_id]
            metric_ids = list(plan_entry.get("metrics", {}).keys())
            logger.info(f"Metric IDs within the test plan: {metric_ids}")

        with open(self.test_plan_file, 'r', encoding='utf-8') as case_file:
            all_cases_by_metric = json.load(case_file)

        # Balanced sampling logic
        num_metrics = len(metric_ids)
        if self.limit:
            base_per_metric = self.limit // num_metrics
            remainder = self.limit % num_metrics
        else:
            base_per_metric = None
            remainder = 0

        total_collected = 0
        for idx, metric_id in enumerate(metric_ids):
            metric_data = all_cases_by_metric.get(metric_id)
            if not metric_data:
                continue
            cases = metric_data.get("cases", [])
            logger.info(f"Metric ID: {metric_id} -> {plan_entry.get('metrics', {}).get(metric_id, metric_id)} has {len(cases)} test cases")

            # Determine how many to sample from this metric
            if self.limit:
                n_to_sample = base_per_metric + (1 if idx < remainder else 0)
                n_to_sample = min(n_to_sample, len(cases))
                sampled_cases = random.sample(cases, n_to_sample) if n_to_sample > 0 else []
            else:
                sampled_cases = cases

            for test_case in sampled_cases:
                logger.info(f"Lining up prompt (PROMPT_ID: {test_case.get('PROMPT_ID')}, metric: {plan_entry.get('metrics', {}).get(metric_id, metric_id)})")
                logger.info(f"Prompt to be sent: {test_case.get('PROMPT')}")

                test_case_id = test_case.get('PROMPT_ID')
                system_prompt = str(test_case.get('SYSTEM_PROMPT', '')).replace("\n", "")
                prompt = str(test_case.get('PROMPT', '')).replace("\n", "")
                prompt_text = f"{system_prompt.strip()} {prompt.strip()}".strip()

                dedup_key = test_case_id or prompt_text
                logger.debug(f"Processing test_case_id: {test_case_id}, dedup_key: {dedup_key}")

                if dedup_key in sent_prompts:
                    logger.debug("-> Skipped (duplicate)")
                    continue
                sent_prompts.add(dedup_key)

                prompt_list.append(prompt_text)
                prompt_id_list.append(test_case_id)
                total_collected += 1

        if not self.client:
            logger.warning("Client is not initialized!")
            results = [{
                "prompt_id": pid,
                "response": "(no client) prompt was: " + p
            } for pid, p in zip(prompt_id_list, prompt_list)]
        else:
            try:
                chat_id = self.assign_chat_id()
                response = self.client.chat(chat_id=chat_id, prompt_list=prompt_list)
                data = response.json()
                if isinstance(data, dict) and "response" in data:
                    resp_list = data["response"]
                    for pid, resp, prompt in zip(prompt_id_list, resp_list, prompt_list):
                        response_text = resp.get("response", "") if isinstance(resp, dict) else str(resp)
                        results.append({
                            "prompt_id": pid,
                            "test_plan_id": self.test_plan_id,
                            "response": response_text
                        })
                else:
                    logger.warning("Unexpected response format for batch prompts")
            except Exception as e:
                logger.error(f"Exception occurred during chat: {e}")
                for pid in prompt_id_list:
                    results.append({
                        "prompt_id": pid,
                        "test_plan_id": self.test_plan_id,
                        "response": f"Error: {e}"
                    })

        result_path = response_file
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("Received responses from the bot and saved to the response file.")
        logger.info(f"Responses saved to {result_path}")
        logger.info(f"Total prompts sent: {len(prompt_list)}")
        logger.info("=== END: send_prompts ===")

        return results


# setting arguments for InterfaceManager Client
client_args = {
        "base_url": args.base_url,
        "application_type": args.application_type,
        "model_name": args.agent_name,
        "openui_email": args.openui_email,
        "openui_password": args.openui_password,
        "run_mode": args.run_mode
    }

# Initialize InterfaceManagerClient
client = InterfaceManagerClient(**client_args)

manager = TestCaseExecutionManager(
        test_plan_file=args.test_plan_file,
        test_plan_id=args.test_plan_id,
        limit=args.test_case_count,
        **client_args
    )

if args.action == "send_all_prompts":
    results = manager.send_all_prompts()
    output_file = str(response_file)
    print(f"Responses saved to {output_file}")
