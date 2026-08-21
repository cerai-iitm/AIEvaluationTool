import os
from dotenv import load_dotenv
import json
import ast
import csv
from .logger import get_logger
from types import SimpleNamespace
import hashlib
from deepeval.metrics.g_eval.schema import Steps, ReasonScore
from ollama import Client, AsyncClient
from deepeval.models.base_model import DeepEvalBaseLLM
from typing import Optional, List

logger = get_logger("utils_new")

class FileLoader:
    """
    run_file_path : should be the __file__
    """
    @staticmethod
    def _load_env_vars(run_file_path:str):
        env_path = os.path.join(os.path.dirname(run_file_path), '.env')
        # check if the .env file exists
        if not os.path.exists(env_path):
            logger.error(f"Could not find the .env file at path : {env_path}. Please make sure to create one and add the required environment variables.")
            exit(1)
        else:
            load_dotenv(env_path)
    
    @staticmethod
    def _load_file_content(run_file_path:str, req_folder_path:str = "", file_name:str = "", **kwargs):
        data_dir = os.path.join(os.path.dirname(run_file_path), req_folder_path) if req_folder_path != '' else os.path.dirname(run_file_path)
        try:
            file_names = os.listdir(data_dir)
        except:
            file_names = list()
            logger.error(f"The path {data_dir} does not exist.")
        file_content = {}
        if file_name != "":
            file_content = FileLoader._fill_values(file_content, data_dir, file_name, multiple=False) # multiple false means only one file
            return file_content
        else:
            strat = kwargs.get("strategy_name")
            if not strat:
                logger.error("Strategy_name was not inilialized.")
                return file_content
            else:
                prefixes = [os.path.commonprefix([strat, f]) for f in file_names]
                longest = max(prefixes, key=len, default=None)
                files = [f for f in file_names if f.startswith(longest) and len(longest) >= len(strat.split("_")[0])] #the length of the prefix should be at least as long as the first word in the strategy name so that longest is not empty, if its empty it matches with all the names
                if len(files) > 0:
                    for f in files:
                        logger.info(f"Using file {f} to load the examples and evaluate the strategy.")
                        file_content = FileLoader._fill_values(file_content, data_dir, f)
                else:
                    logger.error("None of the files in the data/examples directory match the strategy name.")
        return file_content

    @staticmethod
    def _fill_values(file_content:dict, data_dir:str, f:str, multiple:bool = True):
        store_name = f.split(".")[0]
        if(f.split(".")[1] == "json"):
            with open(os.path.join(data_dir, f), "r") as file:
                content = json.load(file)
                if isinstance(content, dict) and not multiple:
                    file_content = content
                else:
                    file_content[store_name] = content
        elif(f.split(".")[1] == "txt"):
            with open(os.path.join(data_dir, f), "r") as file:
                file_content[store_name] = ast.literal_eval(file.read())
        return file_content


    @staticmethod
    def _check_if_present(run_file_path:str, folder_path:str, search_file_name:str):
        if (os.path.exists(os.path.join(os.path.join(os.path.dirname(run_file_path), folder_path), search_file_name))):
            return True
        else:
            return False
    
    @staticmethod
    def _save_values(run_file_path:str, data:dict, data_dir:str, file_name:str):
        ext = file_name.split(".")[1]
        run_file_dir = os.path.dirname(run_file_path)
        with open(os.path.join(os.path.join(run_file_dir, data_dir), file_name), "w") as f:
            if ext == "json":
                json.dump(data, f)
            elif ext == "txt":
                f.write(json.dumps(data))

    @staticmethod
    def dot_dict(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k : FileLoader.dot_dict(v) for k,v in d.items()})
        else:
            return d

    @staticmethod
    def _to_dot_dict(run_file_path:str, dir_file_path:str, **kwargs):
        full_path = os.path.join(os.path.dirname(run_file_path), dir_file_path)
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                data = json.load(f)
            if kwargs.get("simple"):
                def hook(obj):
                    if obj.get("__as_dict__") is True:
                        obj.pop("__as_dict__", None)
                        return obj
                    return SimpleNamespace(**obj)
                return json.loads(json.dumps(data[kwargs.get("strat_name")]), object_hook=hook)
            else:
                return FileLoader.dot_dict(data)
        else:
            logger.error(f"[ERROR] : could not find the path specified : {full_path}")
            return {}
    
    @staticmethod
    def _save_to_csv(run_file_path:str, df:dict, **kwargs):
        folder_path = os.path.join(os.path.dirname(run_file_path), os.path.join(kwargs.get("data_dir"), kwargs.get("save_dir")) )
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        file_path = os.path.join(folder_path, f"{kwargs.get('strat_name')}.csv")
        file_exists = os.path.isfile(file_path)
        hash = hashlib.sha256(df.get("id").encode('utf-8')).hexdigest()[:20]

        if file_exists:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames     
                data = {row["id"] : row for row in reader}
            values = [hash, *df.get("score").values()]
            data.update({hash : {f : v for f, v in zip(fields, values)}}) 
        else:
            fields = ["id", *df.get("score").keys()]
            values = [hash, *df.get("score").values()]
            data = {hash : {f : v for f, v in zip(fields, values)}}

        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data.values())
        logger.info(f"Score and reason saved to : {file_path}")

class CustomOllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name : str, url : str, *args, **kwargs):
        self.model_name = model_name
        self.ollama_url = f"{url.rstrip()}"
        self.ollama_client = Client(host=self.ollama_url)
        self.score_reason = None
        self.steps = None
    
    def generate(self, input : str, *args, **kwargs) -> str:
        messages = [{"role": "user", "content": f'{input} /nothink'}] # nothink allows us to only get the final answer
        response = self.ollama_client.chat(
            model = self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw) # the deepeval library uses different schemas to serialize the JSON, so we return the schemas as required by the library
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = schema_.steps
        return schema_ 
    
    def load_model(self, *args, **kwargs):
        return None
    
    async def a_generate(self, input:str, *args, **kwargs):
        client = AsyncClient(host=self.ollama_url)
        messages = [{"role": "user", "content": f'{input} /nothink'}]
        response = await client.chat(
            model=self.model_name,
            messages=messages,
            format="json"
        )
        raw = json.loads(response.message.content)
        schema_ =  kwargs.get("schema")(**raw)
        if(kwargs.get("schema") is ReasonScore):
            self.score_reason = {"Score": schema_.score, "Reason": schema_.reason}
        if(kwargs.get("schema") is Steps):
            self.steps = {"Steps" : schema_.steps}
        return schema_
    
    def get_model_name(self, *args, **kwargs):
        return self.model_name


class OllamaConnect:
    
    FileLoader._load_env_vars(__file__)
    ollama_url = os.getenv("OLLAMA_URL")
    dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="ollama_comms")

    @staticmethod
    def prompt_model(text:str, fields:List[str], model_names:List[str] = None, options:dict = None) -> List[dict]:
        ollama_client = Client(host=OllamaConnect.ollama_url)
        tries = OllamaConnect.dflt_vals.n_tries
        resp_in_format = []
        models = OllamaConnect.dflt_vals.model_names if model_names is None else model_names
        while(resp_in_format == [] and tries > 0):
            for model in models:
                try:
                    inputs = {
                        "model" : model,
                        "messages" : [
                            {
                                "role" : "user",
                                "content" : f"{text} /nothink",
                            }
                        ],
                        "format":"json",
                    }
                    if options is not None:
                        inputs.update({"options": options})
                    response = ollama_client.chat(**inputs)
                    try:
                        final = json.loads(response.message.content)
                    except:
                        final = {}
                except Exception as e:
                    logger.error(f"Did not receive any response from the model : {model}.")
                    final = {}
                if(OllamaConnect.has_correct_format(final, fields)):
                    resp_in_format.append(final)
                else:
                    logger.error("Response does not contain the required fields or is not in the correct format.")
            tries -= 1
        return resp_in_format
    
    @staticmethod
    def has_correct_format(obj : Optional[dict], fields: List[str]):
        correct = isinstance(obj, dict)
        distinct_set = set(list(obj.keys())).intersection(set(fields))
        if len(distinct_set) > 0:
            for fld in distinct_set:
                correct = correct and fld in fields and isinstance(obj.get(fld), str) 
            return correct
        else:
            return False
    
    @staticmethod
    def get_reason(agent_response:str, score:float, metric_name:str = None, strategy_name:str = None,
                   user_prompt:str = "", target_domain:str = "", **kwargs):
        prompt = OllamaConnect.dflt_vals.reason_prompt.format(
            input_sent=agent_response,
            user_prompt=user_prompt,
            target_domain=target_domain,
            metric=metric_name,
            score=score,
            add_info=kwargs.get("add_info", ""),
        )
        responses = OllamaConnect.prompt_model(prompt, OllamaConnect.dflt_vals.reqd_flds)
        final_rsn = ""
        try:
            if(0 < len(responses) < 2):
                return f"{responses[0]['reason']}"
            elif(len(responses) > 1):
                reasons = [r["reason"] for r in responses]
                for i, r in enumerate(reasons):
                    if i == 0:
                        final_rsn += f"{i+1}. {r}"
                    else:
                        final_rsn += f"\n {i+1}. {r}"
                return final_rsn
            else:
                return ""
        except Exception as e:
            logger.error(f"Error while getting reason for the score : {e}")
            return ""
        
    @staticmethod
    def get_metric_summary(metric_name: str, scores, reasons=None, **kwargs):
        """
        Accepts a list of scores (and optional reasons) for one metric
        and produces a single coherent summary at metric level.
        """

        # --- Normalize scores ---
        values = list(scores) if isinstance(scores, (list, tuple)) else [scores]

        avg_score = round(sum(values) / len(values), 3)
        score_text = f"Average: {avg_score} from {len(values)} samples"

        # --- Prepare reasons block ---
        reason_text = ""
        if reasons:
            items = reasons if isinstance(reasons, (list, tuple)) else [reasons]
            reason_text = "\n".join(f"- {r}" for r in items if r)

        # --- Build prompt ---
        prompt = OllamaConnect.dflt_vals.metric_summary_prompt.format(
            metric=metric_name,
            scores=score_text,
            reasons=reason_text,
            add_info=kwargs.get("add_info", "")
        )

        # --- Call model ---
        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        if not responses:
            return "Could not generate metric summary."

        summaries = [r["summary"] for r in responses]

        return summaries[0] if len(summaries) == 1 else "\n\n".join(
            f"Summary {i+1} : {s}" for i, s in enumerate(summaries)
        )


    @staticmethod
    def get_single_plan_summary(plan_name: str, metrics: dict, **kwargs):

        plan_overview = []

        for metric_name, data in metrics.items():

            if "metric_summary" not in data:
                continue

            plan_overview.append({
                "metric": metric_name,
                "metric_summary": data.get("metric_summary"),
                "testcase_count": len(data.get("Testcases", {}))
            })

        prompt = OllamaConnect.dflt_vals.plan_summary_prompt.format(
            plan=plan_name,
            overview=json.dumps(plan_overview, indent=2),
            add_info=kwargs.get("add_info", "")
        )

        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        return responses[0]["summary"] if responses else "Could not generate plan summary."
        
    @staticmethod
    def get_run_summary(score_card: dict, **kwargs):

        run_overview = []

        for plan_name, metrics in score_card.items():

            if not isinstance(metrics, dict) or plan_name == "PlanSummary":
                continue

            # Grab plan summary from any metric node (they all share it)
            plan_summary = None
            for data in metrics.values():
                if "plan_summary" in data:
                    plan_summary = data["plan_summary"]
                    break

            if not plan_summary:
                continue

            run_overview.append({
                "plan": plan_name,
                "plan_summary": plan_summary
            })

        prompt = OllamaConnect.dflt_vals.run_summary_prompt.format(
            overview=json.dumps(run_overview, indent=2),
            add_info=kwargs.get("add_info", "")
        )

        responses = OllamaConnect.prompt_model(
            prompt,
            OllamaConnect.dflt_vals.reqd_flds
        )

        if not responses:
            return "Could not generate run summary."

        summaries = [r["summary"] for r in responses]

        return summaries[0] if len(summaries) == 1 else "\n\n".join(
            f"Summary {i+1} : {s}" for i, s in enumerate(summaries)
        )


# The EvaluationReport class is responsible for generating a PDF report of the evaluation results. 
# Report Generation class        
from weasyprint import HTML
from datetime import datetime

class EvaluationReport:

    # ---------------------------------------------
    # Count number of plans
    # ---------------------------------------------

    def count_plans(self, rows):

        plans = set()

        for r in rows:
            plans.add(r[0])

        return len(plans)

    def scorecard_to_table(self, score_card):
        # Count actual plans (exclude PlanSummary meta key if present)
        plan_names = [p for p in score_card.keys() if p != "PlanSummary"]
        multiple_plans = len(plan_names) > 1

        # Build headers dynamically
        headers = [
            "Plan Name",
            "Metric Name",
            "Score (0-1)",
            "Metric Summary",
        ]

        if multiple_plans:
            headers.append("Plan Summary")

        rows = []

        for plan_name in plan_names:

            metrics = score_card[plan_name]
            first_metric = True

            for metric_name, metric_data in metrics.items():

                metric_score = metric_data.get("metric_score", "")
                metric_summary = metric_data.get("metric_summary", "")
                plan_summary = metric_data.get("plan_summary", "")

                row = [
                    plan_name,
                    metric_name,
                    str(metric_score),
                    metric_summary,
                ]

                # Only include plan summary column if multiple plans exist
                if multiple_plans:
                    row.append(plan_summary if first_metric else "")

                rows.append(row)

                first_metric = False

        return headers, rows

    # ---------------------------------------------
    # Build HTML rows
    # ---------------------------------------------

    def build_rows(self, rows, include_plan_summary):

        html_rows = ""

        for r in rows:

            plan = r[0]
            metric = r[1]
            score = r[2]
            metric_summary = r[3]
            plan_summary = r[4] if len(r) > 4 else ""

            if include_plan_summary:

                html_rows += f"""
                <tr>
                    <td>{plan}</td>
                    <td>{metric}</td>
                    <td>{score}</td>
                    <td>{metric_summary}</td>
                    <td>{plan_summary}</td>
                </tr>
                """

            else:

                html_rows += f"""
                <tr>
                    <td>{plan}</td>
                    <td>{metric}</td>
                    <td>{score}</td>
                    <td>{metric_summary}</td>
                </tr>
                """

        return html_rows


    # ---------------------------------------------
    # Extract plan summary if only one plan
    # ---------------------------------------------

    def extract_plan_summary(self, score_card):
        for plan in score_card.values():
            for metric in plan.values():
                summary = metric.get("plan_summary")
                if summary:
                    return summary
        return ""

    # ---------------------------------------------
    # Generate HTML
    # ---------------------------------------------

    def generate_html(
        self,
        target_name,
        run_name,
        timestamp,
        total_testcases,
        run_summary,
        headers,
        rows,
        score_card
    ):

        plan_count = self.count_plans(rows)

        include_plan_summary = plan_count > 1

        table_rows = self.build_rows(rows, include_plan_summary)

        # adjust headers
        if include_plan_summary:
            header_html = "".join(f"<th>{h}</th>" for h in headers)
        else:
            header_html = "".join(f"<th>{h}</th>" for h in headers[:-1])

        header_html = "".join(f"<th>{h}</th>" for h in headers)

        # column layout
        if include_plan_summary:

            colgroup = """
            <col style="width:15%">
            <col style="width:20%">
            <col style="width:7%">
            <col style="width:29%">
            <col style="width:29%">
            """

        else:

            colgroup = """
            <col style="width:18%">
            <col style="width:25%">
            <col style="width:7%">
            <col style="width:50%">
            """

        # summary logic
        summary_section = ""

        if include_plan_summary:

            summary_section = f"""
            <h2>Target Evaluation Run Summary</h2>
            <p class="summary">{run_summary}</p>
            """

        else:

            plan_summary = self.extract_plan_summary(score_card)

            summary_section = f"""
            <h2>Target Evaluation Plan Summary</h2>
            <p class="summary">{plan_summary}</p>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>

@page {{
    size:A4;
    margin:20mm;
}}

body {{
    font-family:"Noto Sans", Arial;
    font-size:11px;
    line-height:1.5;
}}

h1 {{
    text-align:center;
}}

table {{
    width:100%;
    border-collapse:collapse;
    table-layout:fixed;
}}

th,td {{
    border:1px solid black;
    padding:6px;
    vertical-align:top;
    word-wrap:break-word;
}}

thead {{
    display:table-header-group;
}}

tr {{
    page-break-inside:avoid;
}}

.keyvalue td {{
    border:none;
}}

.keyvalue td:first-child {{
    width:180px;
    font-weight:bold;
}}

.summary {{
    text-align:justify;
}}

td:nth-child(3), th:nth-child(3) {{
    text-align:center;
}}

</style>

</head>

<body>

<h1>Conversational AI Evaluation Report</h1>

<h2>Experiment Overview</h2>

<table class="keyvalue">

<tr><td>Target Name</td><td>{target_name}</td></tr>
<tr><td>Run Name</td><td>{run_name}</td></tr>
<tr><td>Timestamp</td><td>{timestamp}</td></tr>
<tr><td>Total Test Cases</td><td>{total_testcases}</td></tr>

</table>

{summary_section}

<h2>Scores Table</h2>

<table>

<colgroup>
{colgroup}
</colgroup>

<thead>
<tr>
{header_html}
</tr>
</thead>

<tbody>
{table_rows}
</tbody>

</table>

</body>
</html>
"""

        return html


    # ---------------------------------------------
    # Create PDF
    # ---------------------------------------------

    def create_report(
        self,
        target_name,
        run_name,
        timestamp,
        total_testcases,
        run_summary,
        headers,
        rows,
        score_card,
        output_file
    ):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = self.generate_html(
            target_name,
            run_name,
            timestamp,
            total_testcases,
            run_summary,
            headers,
            rows,
            score_card
        )

        HTML(string=html).write_pdf(output_file)

        return output_file
