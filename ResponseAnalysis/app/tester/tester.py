import sys
import os
import json
from datetime import datetime

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__) + '/../../'))  # Adjust the path to include the parent directory

from lib.data import Prompt, TestCase, Response, TestPlan, Metric, LLMJudgePrompt, Target, Run, RunDetail, Conversation
from lib.orm import DB  # Import the DB class from the orm module


# __len__ __getitem__ __setitem__ __delitem__ __iter__ __contains__
# __enter__ __exit__  contextual management methods for the DB class
# __iter__ __next__ methods for iterating over languages (raise StopIteration when done)

db = DB(db_url="mariadb+mariadbconnector://root:ATmega32*@localhost:3306/aieval", debug=False)

#print("\n".join([str(m) for m in db.metrics]))
#print("\n".join([str(m) for m in db.targets]))
#print("\n".join([str(m) for m in db.runs]))
#print("\n".join([str(m) for m in db.testcases]))

print(db.get_status_by_run_detail_id(1))
print(db.get_status_by_run_id(1))
print(db.get_run_detail_status(run_name="Gooey AI Run #1", testcase_name="P701"))
print(db.get_run_status(run_name="Gooey AI Run #1"))

plans = json.load(open('Data/plans.json', 'r'))
prompts = json.load(open('Data/DataPoints.json', 'r'))

domain_general = db.add_or_get_domain_id(domain_name='general')
domain_agriculture = db.add_or_get_domain_id(domain_name='agriculture')

lang_auto = db.add_or_get_language_id(language_name='auto')

tc = db.fetch_testcase("P601")

# https://www-help-gooey-ai.filesusr.com/html/7f7b6d_ba05c78336ab53c8fe3fcb339272b40f.html
tgt = Target(target_name="Gooey AI", 
             target_type="WhatsApp", 
             target_url="https://www.help.gooey.ai/farmerchat", 
             target_description="Gooey AI is a WhatsApp-based AI assistant for farmers, providing information and assistance on agricultural practices and crop management.",
             target_domain="agriculture",
             target_languages=["english", "telugu", "bhojpuri", "hindi"])    
target_id = db.add_or_get_target(target = tgt)

run = Run(target=tgt.target_name, 
          run_name="Gooey AI Run #1",
          start_ts=datetime.now().isoformat())
run_id = db.add_or_update_testrun(run=run)

tcs = db.get_testcases_by_testplan(plan_name='Language_Support', n=3)
for testcase in tcs:
    print(f"TestCase: {testcase.name}")
    rundetail = RunDetail(run_name="Gooey AI Run #1", plan_name="Language_Support", testcase_name=testcase.name, metric_name=testcase.metric)
    detail_id = db.add_or_update_testrun_detail(run_detail=rundetail)
    conv = Conversation(target=tgt.target_name, 
                        run_detail_id=detail_id, 
                        testcase=testcase.name)
    conv_id = db.add_or_update_conversation(conversation=conv)

    rundetail.status = "RUNNING"
    detail_id = db.add_or_update_testrun_detail(run_detail=rundetail)

    try:
        # Simulate sending the prompt to the agent
        conv.prompt_ts = datetime.now().isoformat()
        db.add_or_update_conversation(conversation=conv)

        # Simulate receiving the agent's response
        # In a real scenario, this would be replaced with the actual agent's response.
        agent_response = "This is a sample response from the agent."
        conv.agent_response = agent_response
        conv.response_ts = datetime.now().isoformat()
        db.add_or_update_conversation(conversation=conv)
        rundetail.status = "COMPLETED"
        detail_id = db.add_or_update_testrun_detail(run_detail=rundetail)

    except Exception as e:
        print(f"Error during conversation processing: {e}")
        rundetail.status = "FAILED"
        detail_id = db.add_or_update_testrun_detail(run_detail=rundetail)
        continue

run_id = db.add_or_update_testrun(run=run)

#run.end_ts = datetime.now().isoformat()
run.status = "RUNNING"

run_id = db.add_or_update_testrun(run=run)

run.end_ts = datetime.now().isoformat()
run.status = "COMPLETED"

run_id = db.add_or_update_testrun(run=run)
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
