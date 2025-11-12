from .strategy_implementor import StrategyImplementor
from lib.data import TestCase, Conversation, Prompt, Response, LLMJudgePrompt
from typing import Tuple
from .utils_new import FileLoader
import random
import os
from .logger import get_logger
import pprint

logger = get_logger("evaluator")
FileLoader._load_env_vars(__file__)

class Evaluator:
    """
    Takes in an examples file, loads it as testcases and conversations and uses the 
    strategy implementor to get individual scores and average score 
    """
    def __init__(self):
        self.runner = StrategyImplementor()
    
    def set_strategy(self, strategy_name:str, metric_name:str):
        self.strat_name = strategy_name
        self.metric_name = metric_name
    
    def get_testcase_obj(self, example:dict) -> Tuple[TestCase, Conversation]:
        """
        this function takes in an example, extracts all the required entities and 
        returns a tuple of TestCase and Conversation objects
        """
        ex = FileLoader.dot_dict(example)
        test_case = TestCase(
            name = f"TC_{random.randint(1,1000)}",
            metric = self.metric_name,
            prompt = Prompt(
                system_prompt = ex.sys_prompt,
                user_prompt = ex.user_prompt
            ),
            strategy = self.strat_name,
            response = Response(
                response_text = ex.expected_output,
                response_type = random.choice("GT", "GTDesc")
            ),
            judge_prompt = LLMJudgePrompt(
                prompt = ex.judge_prmompt
            )
        )
        conversation = Conversation(
            target = f"{random.randint(1, 1000)}",
            testcase = test_case.name,
            run_detail_id = random.randint(1, 1000),
            agent_response = ex.agent_response
        )
        return test_case, conversation
    
    def main(self, strategy_name:str, metric_name:str) -> dict:
        """
        use this function to parse the examples file using the strategy_name, and
        for each example in the file, use the runner to run the example and get the score,
        return the scores in the format : {human_score : , our_score : }

        The examples file must be a json list with each example as a dictionary in the format:
        {
            "judge_prompt" : ,
            "sys_prompt" : ,
            "user_prompt" : ,
            "expected_output" : ,
            "agent_response" : ,
            "response_score" : ,
        }

        The example files must start with the same name as the "strategy file name", not the strategy name

        """
        self.set_strategy(strategy_name, metric_name)
        examples = FileLoader._load_file_content(__file__, os.getenv("EXAMPLES_DIR"), strategy_name=strategy_name)
        print(examples)

        # try:
        #     self.runner.set_metric_strategy(strategy_name, metric_name)
        #     self.runner.execute()
        # except Exception as e:
        #     logger.error(f"Could not find the specified strategy name or the metric name. Additional info : {e}")
            

ev = Evaluator()
ev.main("fluency", "")