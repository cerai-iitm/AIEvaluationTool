
import sys
import os
import json
from datetime import datetime
import argparse

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to include the parent directory

from lib.data import Prompt, TestCase, Response, TestPlan, Metric, LLMJudgePrompt, Target, Run, RunDetail, Conversation
from lib.orm import DB  # Import the DB class from the orm module

plans = json.load(open('Data/plans.json', 'r'))
prompts = json.load(open('Data/DataPoints.json', 'r'))

db = DB(db_url="mariadb+mariadbconnector://root:ATmega32*@localhost:3306/aieval", debug=False)

domain_general = db.add_or_get_domain_id(domain_name='general')
domain_agriculture = db.add_or_get_domain_id(domain_name='agriculture')

lang_auto = db.add_or_get_language_id(language_name='auto')

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
            domain_id = db.add_or_get_domain_id(domain_name=case['DOMAIN'])
        else:
            domain_id = domain_general
        
        prompt = Prompt(system_prompt=case['SYSTEM_PROMPT'], 
                      user_prompt=case['PROMPT'], 
                      domain_id=domain_id, 
                      lang_id=lang_auto)

        strategy = 'auto'
        judge_prompt = None
        if 'LLM_AS_JUDGE' in case and case['LLM_AS_JUDGE'] != "No":
            strategy = 'llm_as_judge'
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
