from DB import DB
import sys
import os
import json

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data import Prompt, TestCase, Response, TestPlan, Metric, LLMJudgePrompt

# __len__ __getitem__ __setitem__ __delitem__ __iter__ __contains__
# __enter__ __exit__  contextual management methods for the DB class
# __iter__ __next__ methods for iterating over languages (raise StopIteration when done)

db = DB(db_url="mariadb+mariadbconnector://root:ATmega32*@localhost:3306/eval", debug=True)

plans = json.load(open('Data/plans.json', 'r'))
prompts = json.load(open('Data/DataPoints.json', 'r'))

domain_general = db.add_or_get_domain_id(domain_name='general')
domain_agriculture = db.add_or_get_domain_id(domain_name='agriculture')

lang_auto = db.add_or_get_language_id(language_name='auto')

db.get_testcases(metric_name='Language_Coverage')

"""
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
    metric_name = metrics_lookup.get(met)
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
                      prompt=prompt, 
                      strategy=strategy, 
                      response=response, 
                      judge_prompt=judge_prompt)
        tcases.append(tc)
    db.add_metric_and_testcases(testcases=tcases, metric=metric_obj)
"""

"""
        
#print("\n".join([repr(_) for _ in db.languages]))
#print(db.get_language_name(2))
lang_english = db.add_or_get_language_id('english')
domain_id = db.add_or_get_domain_id('agriculture')
strategy_id = db.add_or_get_strategy_id('auto')

newPrompt = Prompt(system_prompt="Answer yes or no to the following question.", 
                   user_prompt="Can cotton grow in red soil?",
                   domain_id=domain_id,
                   lang_id=lang_english)

newResponse = Response(response_text="Yes", 
                            response_type='GT', 
                            prompt=newPrompt, 
                            lang_id=lang_english)

#prompt_id = db.add_prompt(newPrompt)
#print(newPrompt, "added with id:", prompt_id)

#tc_id = db.create_testcase(testcase_name="tc1", prompt=newPrompt)
#tc = TestCase(name="tc2", prompt=newPrompt, response=newResponse)
#tc_id = db.create_testcase(tc)

tc = db.add_testcase_from_prompt_id(testcase_name="tc4", 
                                   prompt_id=17,
                                   strategy=strategy_id if strategy_id is not None else "Auto",
                                   response_id=1)

tc = db.fetch_testcase("tc1")
print(f"Test case created with ID: {tc}")
#tc_name = db.testcase_id2name(1)
#print(tc_name)
tc = db.fetch_testcase("tc2")
print (f"Fetched TestCase: {tc}")
"""
