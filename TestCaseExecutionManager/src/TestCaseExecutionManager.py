import json
import argparse
from typing import List, Dict, Union
import sys, os

sys.path.append(os.path.relpath("../.."))
from InterfaceManager import InterfaceManagerClient

parser = argparse.ArgumentParser(description="LLM Evaluation Suite - A comprehensive evaluation tool for verifying conversational AI applications.")

parser.add_argument("--base_url", type=str, default="http://localhost:8000", help="Base URL of the server (Default: 'http://localhost:8000')")
parser.add_argument("--application_type", type=str.upper, default="WHATSAPP_WEB", help="Application type: required for LLM evaluation (e.g., WHATSAPP_WEB or OPENUI)")
parser.add_argument("--model_name", type=str, default="Gooey AI", help="Model name for the application (Default set to Gooey AI)")
parser.add_argument("--openui_email", type=str, help="OpenUI email: required for OpenUI Application")
parser.add_argument("--openui_password", type=str, help="OpenUI password: required for OpenUI Application")
parser.add_argument("--run_mode", default="single_window", type=str, help="How to handle prompt session", choices=["single_window", "multiple_window"])

# group = parser.add_mutually_exclusive_group(required=True)
# group.add_argument("--prompt", type= str, help="Send a single prompt to the conversational AI application")
# group.add_argument("--prompt_from_excel", type=str, default="sample.xlsx", help="Path to Excel file containing prompts")
# group.add_argument("--data", default="test.json", help="Default json file")

parser.add_argument("--test_plan_name", required=True, choices=["Inappropriate Content Detection", "Response Out of Scope"], help="Selection of Test Plan")
parser.add_argument("--n", type=int, help="Number of Prompts to run in a Test Plan", default=2)
parser.add_argument("--action", type=str, help="Send all Prompts", default="send_all_prompts")
parser.add_argument("--test_plan_file", default="test.json", help="Default json file")

args = parser.parse_args()

# Validation based on application type
if args.application_type == "WHATSAPP_WEB":
    if not args.model_name:
        parser.error("--model_name is required when --application_type is 'WHATSAPP_WEB'")
elif args.application_type == "OPENUI":
    missing = []
    if not args.model_name:
        missing.append("--model_name")
    if not args.openui_email:
        missing.append("--openui_email")
    if not args.openui_password:
        missing.append("--openui_password")
    if missing:
        parser.error(f"Missing required arguments for 'OPENUI': {', '.join(missing)}")

class TestCaseExecutionManager:
    def __init__(self, test_plan_file, test_plan_name, limit=None, **client_args):
        self.test_plan_file = test_plan_file
        self.test_plan_name = test_plan_name
        self.limit = limit
        self.test_cases = self.load_test_cases()

        if client_args.get("base_url"):
            self.client = InterfaceManagerClient(**client_args)
            self.client.initialize()
            self.client.sync_config(vars(args))
        else:
            self.client = None

    def load_test_cases(self):
        try:
            with open(self.test_plan_file, 'r', encoding='utf-8') as f:
                all_test_plans = json.load(f)
            if self.test_plan_name not in all_test_plans:
                raise ValueError(f"Test plan '{self.test_plan_name}' not found in the file.")
            cases = all_test_plans[self.test_plan_name]
            return cases[:self.limit] if self.limit else cases
        except FileNotFoundError:
            raise RuntimeError(f"Test plan file '{self.test_plan_file}' not found.")
        except json.JSONDecodeError:
            raise RuntimeError("Test plan file contains invalid JSON.")

    def send(self, chat_id: int, prompt: str) -> Dict[str, Union[str, int]]:
        """
        Sends a single prompt to the client for the given chat_id.
        Returns a dictionary containing the chat_id, prompt, and response.
        """
        if not self.client:
            return {
                "chat_id": chat_id,
                "prompt": prompt,
                "response": "(no client) prompt was: '{}'".format(prompt)
            }

        try:
            response = self.client.chat(chat_id=chat_id, prompt_list=[prompt])
            data = response.json()

            if isinstance(data, list) and data and isinstance(data[0], dict):
                response_text = data[0].get("response", "")
            elif isinstance(data, dict):
                response_text = data.get("response", "")
            else:
                response_text = ""

            return {
                "chat_id": chat_id,
                "prompt": prompt,
                "response": response_text
            }

        except Exception as e:
            return {
                "chat_id": chat_id,
                "prompt": prompt,
                "response": "Error: {}".format(e)
            }

    def get_prompt_list(self) -> List[str]:
        combined_prompts = [
            f"{case['system_prompt']} {case['prompt']}".strip()
            for case in self.test_cases
        ]
        return combined_prompts

    def send_all_prompts(self):
        results = []
        
        # Collect all prompts and their chat_ids
        prompt_list = []
        chat_id_list = []
        for test_case in self.test_cases:
            chat_id = test_case.get("chat_id", "")
            combined_prompt = f"{test_case.get('system_prompt', '')} {test_case.get('prompt', '')}".strip()
            prompt_list.append(combined_prompt)
            chat_id_list.append(chat_id)
        
        if not self.client:
            return [{
                "chat_id": chat_id,
                "prompt": prompt,
                "response": "(no client) prompt was: '{}'".format(prompt)
            } for chat_id, prompt in zip(chat_id_list, prompt_list)]
        
        try:
            response = self.client.chat(chat_id=chat_id_list[0], prompt_list=prompt_list)
            data = response.json()

            response_list = data.get("response", [])

            for i, (chat_id, prompt) in enumerate(zip(chat_id_list, prompt_list)):
                if isinstance(response_list, list) and len(response_list) > i and isinstance(response_list[i], dict):
                    response_text = response_list[i].get("response", "")
                else:
                    response_text = ""
                results.append({
                    "chat_id": chat_id,
                    "prompt": prompt,
                    "response": response_text
                })
        except Exception as e:
            results = [{
                "chat_id": chat_id,
                "prompt": prompt,
                "response": f"Error: {e}"
            } for chat_id, prompt in zip(chat_id_list, prompt_list)]

        return results

# setting arguments for InterfaceManager Client
client_args = {
        "base_url": args.base_url,
        "application_type": args.application_type,
        "model_name": args.model_name,
        "openui_email": args.openui_email,
        "openui_password": args.openui_password,
        "run_mode": args.run_mode
    }

# Initialize InterfaceManagerClient
client = InterfaceManagerClient(**client_args)

manager = TestCaseExecutionManager(
        test_plan_file=args.test_plan_file,
        test_plan_name=args.test_plan_name,
        limit=args.n,
        **client_args
    )

if args.action == "send_all_prompts":
    results = manager.send_all_prompts()
    for r in results:
        print(json.dumps(r, indent=2))
