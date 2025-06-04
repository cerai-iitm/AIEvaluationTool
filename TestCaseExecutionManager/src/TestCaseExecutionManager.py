import json
import argparse
from typing import List, Dict, Union
import sys, os


sys.path.append(os.path.relpath("../.."))
from InterfaceManager import InterfaceManagerClient

parser = argparse.ArgumentParser(description="LLM Evaluation Suite - A comprehensive evaluation tool for verifying conversational AI applications.")

parser.add_argument("--base_url", type=str, default="http://localhost:8000", help="Base URL of the server (Default: 'http://localhost:8000')")
parser.add_argument("--application_type", type=str.upper, default="WHATSAPP_WEB", help="Application type: required for LLM evaluation (e.g., WHATSAPP_WEB or OPENUI)")
parser.add_argument("--model_name", type=str, default="Gooey AI", help="Model name for the application (Default set to ChatGPT)")
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
    
) # Add more to this list
parser.add_argument("--n", type=int, help="Number of Prompts to run in a Test Plan", default=2)
parser.add_argument("--action", type=str, help="Send all Prompts", default="send_all_prompts")
parser.add_argument("--test_plan_file", default="DataPoints.json", help="Default json file")

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

            with open("plans.json", 'r', encoding='utf-8') as plan_file:
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
            response = self.client.chat(chat_id=chat_id, prompt_list=[prompt])
            data = response.json()

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

    def get_prompt_list(self):
        combined_prompts = [
            f"{case['System_Prompt']} {case.get('Input')}".strip()
            for case in self.test_cases
        ]
        print(combined_prompts)

    def send_all_prompts(self):
        results = []
        prompt_list = []
        chat_id_list = []
        sent_prompts = set() 
    
        with open("plans.json", 'r', encoding='utf-8') as plan_file:
            all_plans = json.load(plan_file)
            plan_entry = all_plans[self.test_plan_id]
            metric_ids = list(plan_entry.get("metrics", {}).keys())

        with open(self.test_plan_file, 'r', encoding='utf-8') as case_file:
            all_cases_by_metric = json.load(case_file)

        for metric_id in metric_ids:
            metric_data = all_cases_by_metric.get(metric_id)
            if not metric_data:
                continue
            cases = metric_data.get("cases", [])
            for test_case in cases[:self.limit] if self.limit else cases:
                test_case_id = test_case.get('id')
                prompt_text = str(test_case.get('System_Prompt', '')) + ' ' + str(test_case.get('Input', ''))
                dedup_key = test_case_id if test_case_id is not None else prompt_text
                if dedup_key in sent_prompts:
                    continue 
                sent_prompts.add(dedup_key)
                chat_id = self.assign_chat_id()
                expected_output = str(test_case.get('Expected_Output', '')) + ' '+str(test_case.get('Llm_as_judge', ''))
                chat_id_list.append(chat_id)
                prompt_list.append(prompt_text)
                prompt_id = str(test_case.get('Prompt_ID', ''))

            if not self.client:
                    print("Client is not initialized!")
                    results.append({
                        "prompt_id": prompt_id,
                        "expected_output": expected_output,
                        "response": f"(no client) prompt was: {prompt_text}"
                    })
            else:
                    try:
                        response = self.client.chat(chat_id=chat_id, prompt_list=[prompt_text])
                        data = response.json()
                        #print(f"Parsed response: {data}")
                        if isinstance(data, dict) and "response" in data:
                            resp = data["response"]
                            if isinstance(resp, list) and resp and isinstance(resp[0], dict):
                                response_text = resp[0].get("response", "")
                            else:
                                response_text = str(resp)
                        else:
                            response_text = ""
                        results.append({
                            "prompt_id": prompt_id,
                            "test_plan_id": self.test_plan_id,
                            "response": response_text
                        })
                    except Exception as e:
                        print(f"Exception occurred: {e}")
                        results.append({
                            "prompt_id": prompt_id,
                            "test_plan_id": self.test_plan_id,
                            "response": f"Error: {e}"
                        })

        print(prompt_list) 
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
        test_plan_id=args.test_plan_id,
        limit=args.n,
        **client_args
    )

if args.action == "send_all_prompts":
    results = manager.send_all_prompts()

    output_file = "responses.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Responses saved to {output_file}")
