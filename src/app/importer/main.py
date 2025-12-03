
import sys
import os
import json
from datetime import datetime
import argparse
import logging
# import pdb

# pdb.set_trace()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch_formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)7s|%(funcName)s|%(message)s") # 
ch.setFormatter(ch_formatter)
logger.addHandler(ch)

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to include the parent directory



from lib.data import Prompt, TestCase, Response, TestPlan, Metric, LLMJudgePrompt, Target, Run, RunDetail, Conversation

from lib.orm import DB  # Import the DB class from the orm module

# adding arguments for including configuration
parser = argparse.ArgumentParser(description="Data Importer")
parser.add_argument("--config", dest="config", type=str, default="config.json", help="Path to the configuration file")
parser.add_argument("--orm-debug", dest="orm_debug", default=False, action='store_true', help="Enable ORM debug mode")

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

strategies = json.load(open(config['files']['strategies'], 'r'))

# import all the strategies.
logger.debug("Importing strategies...")
for item in strategies.keys():
    strategy_name = strategies[item]
    logger.debug(f"Adding strategy: {strategy_name}")    
    db.add_or_get_strategy_id(strategy_name=strategy_name)

domain_general = db.add_or_get_domain_id(domain_name='general')
lang_auto = db.add_or_get_language_id(language_name='auto')

# load the test plans and metrics.
logger.debug("Importing test plans and metrics...")
metrics_lookup = {}
for plan in plans.keys():
    record = plans[plan]
    plan_name = record['TestPlan_name']
    test_plan = TestPlan(plan_name=plan_name)
    metrics_list = []
    for metric in record['metrics'].keys():
        metric_name = record['metrics'][metric]
        metrics_lookup[metric] = metric_name
        metric_obj = Metric(metric_name=metric_name, domain_id=domain_general if domain_general is not None else 1)
        metrics_list.append(metric_obj)

    db.add_testplan_and_metrics(plan=test_plan, metrics=metrics_list)

for met in prompts.keys():
    if met not in metrics_lookup:
        print(f"Warning: Metric '{met}' not found in plans. Skipping...")
        continue
    metric_name = metrics_lookup.get(met, "Unknown Metric")
    metric_obj = Metric(metric_name=str(metric_name), domain_id=domain_general)

    testcases = prompts[met]["cases"]

    tcases = []
    for case in testcases:
        if 'DOMAIN' in case:
            domain_name = case['DOMAIN'].lower()
            domain_id = db.add_or_get_domain_id(domain_name=domain_name)
        else:
            domain_id = domain_general
        
        prompt = Prompt(system_prompt=case['SYSTEM_PROMPT'], 
                      user_prompt=case['PROMPT'], 
                      domain_id=domain_id, 
                      lang_id=lang_auto)
        
        strategy = 'auto'
        if 'STRATEGY' in case:
            strategy_id = case['STRATEGY']
            if len(strategy_id) > 0 and strategy_id[0] not in strategies:
                logger.error(f"Strategy '{strategy}' not found in strategies. Skipping...")
                continue
            strategy = strategies[strategy_id[0]].lower()
            
        judge_prompt = None
        if 'LLM_AS_JUDGE' in case and case['LLM_AS_JUDGE'] != "No":
            judge_prompt = LLMJudgePrompt(prompt=case['LLM_AS_JUDGE'])

        response = None
        if 'EXPECTED_OUTPUT' in case:
            response = Response(response_text=case['EXPECTED_OUTPUT'], 
                                response_type='GT', 
                                lang_id=lang_auto)
        
        tc = TestCase(name=case['PROMPT_ID'], 
                      metric=metric_name,
                      prompt=prompt, 
                      strategy=strategy, 
                      response=response, 
                      judge_prompt=judge_prompt)
        tcases.append(tc)
    db.add_metric_and_testcases(testcases=tcases, metric=metric_obj)

tgt = Target(target_name="Gooey AI", 
             target_type="WhatsApp", 
             target_url="https://www.help.gooey.ai/farmerchat", 
             target_description="Gooey AI is a WhatsApp-based AI assistant for farmers, providing information and assistance on agricultural practices and crop management.",
             target_domain="agriculture",
             target_languages=["english", "telugu", "bhojpuri", "hindi"])    
target_id = db.add_or_get_target(target = tgt)

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


tgt = Target(target_name="CPGRAMS", 
             target_type="WebApp", 
             target_url="https://cpgramsaichatbot.com/", 
             target_description="CPGRAMS is a web-based AI assistant for streamlines public grievance registration, tracking, and monitoring to enhance efficiency, transparency, and citizen engagement in governance.",
             target_domain="government services",
             target_languages=["english","assamese","bengali","bodo","dogri","goan konkani","gujarati","hindi","kannada","kashmiri","maithili","malayalam","manipuri","marathi","nepali","odia","punjabi","sanskrit","santali","sindhi","tamil","telugu","urudu"])
target_id = db.add_or_get_target(target = tgt)

tgt = Target(target_name="OPENWEB-UI", 
             target_type="WebApp", 
             target_url="http://localhost:3000", 
             target_description="OpenWeb UI is an open-source, browser-based interface designed for interacting with large language models (LLMs) and AI agents.",
             target_domain="LLM Interface",
             target_languages=["english"])
target_id = db.add_or_get_target(target = tgt)