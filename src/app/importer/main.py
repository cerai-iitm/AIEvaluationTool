import sys
import os
import json
from datetime import datetime
import argparse
import logging
# import pdb

# pdb.set_trace()

# # Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch_formatter = logging.Formatter(
    "%(asctime)s|%(name)s|%(levelname)7s|%(funcName)s|%(message)s"
)  #
ch.setFormatter(ch_formatter)
logger.addHandler(ch)

# logging.disable(logging.CRITICAL)

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to include the parent directory



from lib.data import Prompt, TestCase, Response, TestPlan, Metric, LLMJudgePrompt, Target, Run, RunDetail, Conversation

from lib.orm import DB  # Import the DB class from the orm module

#----------------------remove the code below in production----------------------
# Silence everything except your manual prints
# logging.getLogger().setLevel(logging.CRITICAL)
# logging.getLogger('lib.orm.DB').setLevel(logging.CRITICAL) 
# logging.getLogger('lib.data').setLevel(logging.CRITICAL)
#----------------------remove the code below in production----------------------

# Helper function to parse SUB_METRIC and convert to CamelCase
def parse_and_format_submetric(sub_metric_str):
    """
    Parse SUB_METRIC and convert to CamelCase with underscores
    
    Examples:
    - "privacy_leakage/nan" → "Privacy_leakage"
    - "toxicity_level/contextual_or_conversational_toxicity" → "Toxicity_Level/Contextual_Or_Conversational_Toxicity"
    """
    if not sub_metric_str or "/" not in sub_metric_str:
        return None
    
    parts = sub_metric_str.split("/")
    
    # If second part is "nan", use only first part; otherwise use full metric with slash
    if len(parts) > 1 and parts[1].lower() != "nan":
        # Use full metric: "part1/part2" in CamelCase
        part1_camel = "_".join(word.capitalize() for word in parts[0].split("_"))
        part2_camel = "_".join(word.capitalize() for word in parts[1].split("_"))
        return f"{part1_camel}/{part2_camel}"
    else:
        # Use only first part in CamelCase
        metric_part = parts[0]
        camel_case = "_".join(word.capitalize() for word in metric_part.split("_"))
        return camel_case

# adding arguments for including configuration
parser = argparse.ArgumentParser(description="Data Importer")
parser.add_argument(
    "--config",
    dest="config",
    type=str,
    default="config.json",
    help="Path to the configuration file",
)
parser.add_argument(
    "--orm-debug",
    dest="orm_debug",
    default=False,
    action="store_true",
    help="Enable ORM debug mode",
)

args = parser.parse_args()

# connecting to the database
config = json.load(open(args.config, 'r'))
# db_url = "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}".format(
#     user=config['db']['user'],
#     password=config['db']['password'],
#     host=config['db']['host'],
#     port=config['db']['port'],
#     database=config['db']['database']
# )

# Build DB URL based on engine type
engine = config['db'].get('engine', 'sqlite').lower()

if engine == "sqlite":
    sqlite_file = config['db'].get('file', 'app.db')

    # project_root = src/app/importer/../../../
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

    # Put DB in project_root/data
    db_folder = os.path.join(base_dir, "data")
    os.makedirs(db_folder, exist_ok=True)

    db_path = os.path.join(db_folder, sqlite_file)
    db_url = f"sqlite:///{db_path}"

elif engine == "mariadb":
    db_url = (
        "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}"
        .format(
            user=config['db']['user'],
            password=config['db']['password'],
            host=config['db']['host'],
            port=config['db']['port'],
            database=config['db']['database']
        )
    )

else:
    raise ValueError(f"Unsupported database engine: {engine}")

plans = json.load(open(config['files']['plans'], 'r'))
#testcases -> basically the data points
prompts = json.load(open(config['files']['testcases'], 'r'))

db = DB(db_url=db_url, debug=args.orm_debug)

strategies = json.load(open(config["files"]["strategies"], "r"))
descriptions = json.load(open(config["files"]["descriptions"], "r"))

# Build one case-insensitive lookup for parent metrics and Parent/SubMetric rows.
metric_descriptions = {}
for plan_metrics in descriptions.values():
    for metric_name, metric_data in plan_metrics.items():
        metric_description = metric_data.get("description")
        if metric_description:
            metric_descriptions[metric_name.lower()] = metric_description

        for submetric_name, submetric_data in metric_data.get("sub_metrics", {}).items():
            submetric_description = submetric_data.get("description")
            if submetric_description:
                lookup_key = f"{metric_name}/{submetric_name}".lower()
                metric_descriptions[lookup_key] = submetric_description

# import all the strategies.
logger.debug("Importing strategies...")
for strategy_id, strategy_data in strategies.items():
    strategy_name = strategy_data["name"]
    strategy_description = strategy_data.get("description")
    logger.debug(f"Adding strategy: {strategy_name}")
    db.add_or_get_strategy_id(strategy_name=strategy_name,strategy_description=strategy_description)

domain_general = db.add_or_get_domain_id(domain_name="general")
lang_auto = db.add_or_get_language_id(language_name="auto")

# load the test plans and metrics.
logger.debug("Importing test plans and metrics...")
metrics_lookup = {}  # Key: metric_key_lowercase, Value: metric_name_formatted
all_metrics_set = set()  # Track all metrics in lowercase for uniqueness

# First, load metrics from plans.json
for plan in plans.keys():
    record = plans[plan]
    plan_name = record["TestPlan_name"]
    test_plan = TestPlan(
        plan_name=plan_name,
        plan_description=record.get("TestPlan_description"),
    )
    metrics_list = []
    for metric in record["metrics"].keys():
        metric_name = record["metrics"][metric]
        metric_key_lower = metric_name.lower()  # Normalize to lowercase for uniqueness check
        if metric_key_lower not in all_metrics_set:
            all_metrics_set.add(metric_key_lower)
            metrics_lookup[metric] = metric_name
            metric_obj = Metric(
                metric_name=metric_name,
                domain_id=domain_general if domain_general is not None else 1,
                metric_description=metric_descriptions.get(metric_name.lower()),
            )
            metrics_list.append(metric_obj)

    db.add_testplan_and_metrics(plan=test_plan, metrics=metrics_list)

# Second, extract and add SUB_METRIC from test cases
logger.debug("Extracting SUB_METRIC from test cases...")
for met in prompts.keys():
    testcases = prompts[met].get("cases", [])
    for case in testcases:
        if "SUB_METRIC" in case:
            formatted_metric = parse_and_format_submetric(case["SUB_METRIC"])
            if formatted_metric:
                metric_key_lower = formatted_metric.lower()  # Normalize to lowercase
                
                # Only add if not already registered (by lowercase comparison)
                if metric_key_lower not in all_metrics_set:
                    all_metrics_set.add(metric_key_lower)

for met in prompts.keys():
    if met not in metrics_lookup:
        # print(f"Warning: Metric '{met}' not found in plans. Skipping...")
        continue
    parent_metric_name = metrics_lookup.get(met, "Unknown Metric")
    testcases = prompts[met]["cases"]

    # Two-phase grouping: parent metrics first, then child (sub-metrics).
    parent_metric_batches = {}
    child_metric_batches = {}

    for case in testcases:
        formatted_sub_metric = None
        if "SUB_METRIC" in case:
            formatted_sub_metric = parse_and_format_submetric(case["SUB_METRIC"])
        
        if "DOMAIN" in case:
            domain_name = case["DOMAIN"].lower()
            domain_id = db.add_or_get_domain_id(domain_name=domain_name)
        else:
            domain_id = domain_general

        if "LANGUAGE" in case:
            language_name = case["LANGUAGE"].lower()
            lang_id = db.add_or_get_language_id(language_name=language_name)
        else:
            lang_id = lang_auto

        prompt = Prompt(
            system_prompt=case["SYSTEM_PROMPT"],
            user_prompt=case["PROMPT"],
            domain_id=domain_id,
            lang_id=lang_id,
        )

        strategy = "auto"
        if "STRATEGY" in case:
            strategy_id = case["STRATEGY"]
            if len(strategy_id) > 0 and strategy_id[0] not in strategies:
                logger.error(
                    f"Strategy '{strategy}' not found in strategies. Skipping..."
                )
                continue
            strategy = strategies[strategy_id[0]]["name"].lower()

        judge_prompt = None
        if "LLM_AS_JUDGE" in case and case["LLM_AS_JUDGE"] != "No":
            judge_prompt = LLMJudgePrompt(prompt=case["LLM_AS_JUDGE"])

        response = None
        if "EXPECTED_OUTPUT" in case:
            response = Response(
                response_text=case["EXPECTED_OUTPUT"],
                response_type="GT",
                lang_id=lang_id,
            )

        # Base testcase data is reused for parent and child metric batches.
        tc_base = TestCase(
            name=case["PROMPT_ID"],
            metric=parent_metric_name,
            prompt=prompt,
            strategy=strategy,
            response=response,
            judge_prompt=judge_prompt,
        )

        parent_metric_batches.setdefault(parent_metric_name, []).append(tc_base)

        if formatted_sub_metric and formatted_sub_metric.lower() != parent_metric_name.lower():
            child_metric_batches.setdefault(formatted_sub_metric, []).append(tc_base)

    # Phase 1: add parent metric associations first.
    for metric_name_key, base_cases in parent_metric_batches.items():
        mapped_cases = [
            TestCase(
                name=t.name,
                metric=metric_name_key,
                prompt=t.prompt,
                strategy=t.strategy,
                response=t.response,
                judge_prompt=t.judge_prompt,
            )
            for t in base_cases
        ]
        # print(f"Adding metric '{metric_name_key}' with {len(mapped_cases)} test cases to the database.")
        metric_obj = Metric(
            metric_name=str(metric_name_key),
            domain_id=domain_general,
            metric_description=metric_descriptions.get(metric_name_key.lower()),
        )
        db.add_metric_and_testcases(testcases=mapped_cases, metric=metric_obj)

    # Phase 2: add child metric associations.
    for metric_name_key, base_cases in child_metric_batches.items():
        mapped_cases = [
            TestCase(
                name=t.name,
                metric=metric_name_key,
                prompt=t.prompt,
                strategy=t.strategy,
                response=t.response,
                judge_prompt=t.judge_prompt,
            )
            for t in base_cases
        ]
        # print(f"Adding metric '{metric_name_key}' with {len(mapped_cases)} test cases to the database.")
        metric_obj = Metric(
            metric_name=str(metric_name_key),
            domain_id=domain_general,
            metric_description=metric_descriptions.get(metric_name_key.lower()),
        )
        db.add_metric_and_testcases(testcases=mapped_cases, metric=metric_obj)

tgt = Target(
    target_name="Gooey AI",
    target_type="WhatsApp",
    target_url="https://www.help.gooey.ai/farmerchat",
    target_description="Gooey AI is a WhatsApp-based AI assistant for farmers, providing information and assistance on agricultural practices and crop management.",
    target_domain="agriculture",
    target_languages=["english", "telugu", "bhojpuri", "hindi"],
)
target_id = db.add_or_get_target(target=tgt)

tgt = Target(target_name="August AI", 
             target_type="WhatsApp", 
             target_url="https://wa.me/8738030604", 
             target_description="August AI is a WhatsApp-based AI assistant for providing healthcare advices.",
             target_domain="healthcare",
             target_languages=["english", "telugu", "kannada", "hindi", "bengali", "gujarati", "marathi"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="Vaidya AI", 
             target_type="WhatsApp", 
             target_url="https://wa.me/8828808350", 
             target_description="Vaidya AI is a WhatsApp-based AI assistant for providing healthcare advices.",
             target_domain="healthcare",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="Jivi AI", 
             target_type="WhatsApp", 
             target_url="https://wa.me/8121839444", 
             target_description="Jivi AI is a generative AI startup with the vision to harness artificial intelligence to enhance patient care. The platform accelerates diagnostics and ensures higher accuracy, enabling timely and precise treatment for all.",
             target_domain="healthcare",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="FarmSawa", 
             target_type="WhatsApp", 
             target_url="https://wa.me/+254704582362", 
             target_description="FarmSawa is an AI-powered WhatsApp platform designed to support farmers with crop and disease identification, real-time advice, supplier connections and latest market prices.",
             target_domain="healthcare",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="OPENWEB-UI", 
             target_type="WebApp", 
             target_url="http://localhost:3000", 
             target_description="OpenWeb UI is an open-source, browser-based interface designed for interacting with large language models (LLMs) and AI agents.",
             target_domain="general",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

# We don't need to use url for testing gemini api, because we use python client to connect to gemini, url is just a placeholder.
tgt = Target(target_name="Gemini-2.5-Flash", 
             target_type="API",
             target_url="https://ai.google.dev/gemini-api/docs", 
             target_description="GEMINI 2.5 Flash is a state-of-the-art language model developed by Google, designed to deliver advanced natural language understanding and generation capabilities for a wide range of applications.",
             target_domain="general",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="Gemma3n:e2b", 
             target_type="API",
             target_url="http://localhost:11434", 
             target_description="Gemma3n:e2b is a local deployment of the Gemini 3n language model, optimized for efficient performance and tailored applications.",
             target_domain="general",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="FarmerChat",
             target_type="WebApp", 
             target_url="https://www-help-gooey-ai.filesusr.com/html/18ec4d_3005ee787398e60b1e5b118078b53f5b.html", 
             target_description="FarmerChat is a web-based platform that connects farmers with agricultural experts for real-time advice and support.",
             target_domain="agriculture",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)
