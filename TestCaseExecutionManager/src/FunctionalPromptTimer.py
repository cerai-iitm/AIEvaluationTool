import json
import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Set project root and path
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]
sys.path.append(str(project_root))

from InterfaceManager import InterfaceManagerClient

# Data paths
plans_path = project_root / "Data" / "plans.json"
data_points_path = project_root / "Data" / "DataPoints.json"

class FunctionalPromptTimer:
    def __init__(
        self,
        test_plan_id: str,
        agent_name: str,
        base_url: str = "http://localhost:8000",
        run_mode: str = "single_window",
        test_case_count: int = 2,
        test_plan_file: str = str(data_points_path),
        domain: str = None,
    ):
        self.test_plan_id = test_plan_id
        self.agent_name = agent_name
        self.base_url = base_url
        self.run_mode = run_mode
        self.test_case_count = test_case_count
        self.test_plan_file = test_plan_file
        self.domain = domain
        self.chat_id_counter = 0

        self.client_args = {
            "base_url": self.base_url,
            "application_type": "WHATSAPP_WEB",
            "model_name": self.agent_name,
            "run_mode": self.run_mode,
        }

        self.client = InterfaceManagerClient(**self.client_args)
        self.client.initialize()
        self.client.sync_config(self.client_args)

    def assign_chat_id(self) -> int:
        chat_id = self.chat_id_counter
        self.chat_id_counter += 1
        return chat_id

    def collect_prompt_timings(self) -> List[Dict[str, Any]]:
        """
        Sends prompts under a single session and returns timing info.
        Each result contains: prompt_id, response, start_time, end_time
        """
        prompt_list = []
        prompt_id_list = []
        sent_prompts = set()

        # Load test plan and metric IDs
        with open(plans_path, "r", encoding="utf-8") as f:
            all_plans = json.load(f)
        plan_entry = all_plans.get(self.test_plan_id, {})
        metric_ids = list(plan_entry.get("metrics", {}).keys())

        # Load test cases
        with open(self.test_plan_file, "r", encoding="utf-8") as f:
            all_cases_by_metric = json.load(f)

        for metric_id in metric_ids:
            metric_cases = all_cases_by_metric.get(metric_id, {}).get("cases", [])
            if self.domain:
                metric_cases = [c for c in metric_cases if c.get("DOMAIN", "").lower() == self.domain.lower()]
            for case in metric_cases[:self.test_case_count]:
                prompt_id = case.get("PROMPT_ID")
                prompt = f"{case.get('SYSTEM_PROMPT', '').strip()} {case.get('PROMPT', '').strip()}"
                if prompt_id in sent_prompts:
                    continue
                sent_prompts.add(prompt_id)
                prompt_list.append(prompt)
                prompt_id_list.append(prompt_id)

        chat_id = self.assign_chat_id()
        results = []

        for pid, prompt in zip(prompt_id_list, prompt_list):
            try:
                start_dt = datetime.utcnow()
                start_time = start_dt.isoformat()

                response = self.client.chat(chat_id=chat_id, prompt_list=[prompt])

                end_dt = datetime.utcnow()
                end_time = end_dt.isoformat()

                data = response.json()
                resp_text = ""
                if isinstance(data.get("response"), list) and isinstance(data["response"][0], dict):
                    resp_text = data["response"][0].get("response", "")
                else:
                    resp_text = str(data.get("response", ""))

                results.append({
                    "prompt_id": pid,
                    "response": resp_text,
                    "start_time": start_time,
                    "end_time": end_time
                })

            except Exception as e:
                results.append({
                    "prompt_id": pid,
                    "response": f"Error: {e}",
                    "start_time": start_time,
                    "end_time": datetime.utcnow().isoformat()
                })

        return results
