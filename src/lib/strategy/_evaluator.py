from .strategy_implementor import StrategyImplementor
from lib.data import TestCase, Conversation, Prompt, Response, LLMJudgePrompt
from typing import Tuple
from .utils_new import FileLoader
import random
import os
from .logger import get_logger
import numpy as np
import json
import random

logger = get_logger("evaluator")
FileLoader._load_env_vars(__file__)
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="_evaluator")

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
        self.data_dir = os.getenv("DATA_PATH")
    
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

    def save_scores(self, strat_name:str, score:dict, to_json:bool = True, **kwargs):
        if to_json:
            if(not FileLoader._check_if_present(__file__, self.data_dir, f"{dflt_vals.score_file}.json")):
                score_data = {}
            else:
                score_data =  FileLoader._load_file_content(__file__, self.data_dir, file_name=f"{dflt_vals.score_file}.json")
            score_data[strat_name] = score
            FileLoader._save_values(__file__, score_data, self.data_dir, f"{dflt_vals.score_file}.json")
        else:
            concatted = "\n".join(list(kwargs.get("ex").values())[:3]) # basically we are joing first three values of the example, ie judge, sys and user prompts
            FileLoader._save_to_csv(__file__, {"id" : concatted, "score" : score}, strat_name=strat_name, data_dir="data", save_dir="scores_csv")
    
    def main(self, strategy_name:str = "", metric_name:str = ""):
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

        The example files must start with the same name as the value of the "name" inside the strategy file.
        e.g. for llm_judge_poitive or negative, the example file should be llm_judge (file that contains the strat)

        """
        self.set_strategy(strategy_name, metric_name)
        examples = FileLoader._load_file_content(__file__, os.getenv("EXAMPLES_DIR"), strategy_name=strategy_name)
        if len(examples) < 1:
            logger.error(f"Could not find files with example data for {strategy_name} strategy in data/examples/.")
            return examples
        combined = self.combine_examples(examples)
        assigned_scores, human_scores = [], []
        for ex_list in combined.values():
            random.shuffle(ex_list)
            for i, example in enumerate(ex_list[:10]):
                self.runner.set_metric_strategy(strategy_name, metric_name)
                try:
                    objects = self.get_testcase_obj(example)
                    curr_score, reason = self.runner.execute(*objects)
                    logger.info(f"Score : {curr_score}, Reasoning : {reason}")
                    assigned_scores.append(curr_score)
                    human_scores.append(example["response_score"])
                except Exception as e:
                    logger.error(f"Could not find the specified strategy name or the metric name. Additional info : {e}")
                self.save_scores(strategy_name, 
                                {"evaluated_score" : curr_score, "human_score" : example["response_score"], "reason" : reason},
                                to_json= False, ex = example)
                avg_score = round(np.mean(assigned_scores), 3)
                human_score = round(np.mean(human_scores), 3)
                logger.info(f"The average score for {strategy_name} based on the evaluation of examples is : {avg_score}")
                logger.info(f"The average human score for {strategy_name} is : {human_score}")
                if i % dflt_vals.checkpoint == 0 and i != 0: 
                    self.save_scores(strategy_name, {"evaluated_score" : avg_score, "human_score" : human_score})
                
ev = Evaluator()
ev.main(strategy_name="entity_recognition", metric_name="")