from .strategy_implementor import StrategyImplementor
from lib.data import TestCase, Conversation, Prompt, Response, LLMJudgePrompt
from typing import Tuple
from .utils_new import FileLoader
import random
import os
from .logger import get_logger
import numpy as np

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
                response_type = random.choice(["GT", "GTDesc"])
            ),
            judge_prompt = LLMJudgePrompt(
                prompt = ex.judge_prompt
            )
        )
        conversation = Conversation(
            target = f"{random.randint(1, 1000)}",
            testcase = test_case.name,
            run_detail_id = random.randint(1, 1000),
            agent_response = ex.agent_response
        )
        return test_case, conversation
    
    def combine_examples(self, multiple_examples:dict):
        combined = {}
        name = os.path.commonprefix(list(multiple_examples.keys()))
        name = name.removesuffix("_")
        for _, v in multiple_examples.items():
            if(isinstance(v, list)):
                if name in combined:
                    combined[name] += v
                else:
                    combined[name] = v
        return combined
    
    def main(self, strategy_name:str = "", metric_name:str = "") -> dict:
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

        The example files must start with the same name as the strategy name in the strategy file, not the actual strategy name
        e.g. llm_judge, not llm_judge_positive

        """
        self.set_strategy(strategy_name, metric_name)
        examples = FileLoader._load_file_content(__file__, os.getenv("EXAMPLES_DIR"), strategy_name=strategy_name)
        if len(examples) < 1:
            logger.error("Could not find files for the specified strategy.")
            return examples
        combined = self.combine_examples(examples)
        scores = []
        for ex_list in combined.values():
            for example in ex_list[:1]: #later do for all the examples, just for now we are taking 5 examples
                self.runner.set_metric_strategy(strategy_name, metric_name)
                try:
                    scores.append(self.runner.execute(*self.get_testcase_obj(example)))
                except Exception as e:
                    logger.error(f"Could not find the specified strategy name or the metric name. Additional info : {e}")
        avg_score = np.mean(scores)
        logger.info(f"The everage score for {strategy_name} based on the evaluation of examples is : {avg_score}")
        return avg_score
                
ev = Evaluator()
ev.main(strategy_name="llm_judge_positive", metric_name="Inclusivity")