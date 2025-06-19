from DB import DB
import sys
import os

# setup the relative import path for data module.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data import Prompt, TestCase, Response

# __len__ __getitem__ __setitem__ __delitem__ __iter__ __contains__
# __enter__ __exit__  contextual management methods for the DB class
# __iter__ __next__ methods for iterating over languages (raise StopIteration when done)

db = DB(debug=False)


#print("\n".join([repr(_) for _ in db.languages]))
#print(db.get_language_name(2))
lang_english = db.get_language_id('english')
domain_id = db.get_domain_id('agriculture')
strategy_id = db.get_strategy_id('Auto')

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

