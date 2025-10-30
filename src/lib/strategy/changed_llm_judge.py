import warnings
# from .strategy_base import Strategy
from dotenv import load_dotenv
import os, sys
from os.path import join, dirname
# from lib.utils import get_logger
import json
from types import SimpleNamespace
from typing import Optional
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from deepeval.metrics.g_eval.schema import Steps, ReasonScore
from ollama import Client, AsyncClient
from pydantic import BaseModel
from pprint import pprint

from .strategy_base import Strategy
sys.path.append(os.path.dirname(__file__) + '/..')
from lib.utils import get_logger

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

warnings.filterwarnings("ignore")

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, os.getenv("DEFAULT_VALUES_PATH")), "r") as f:
    vals = json.load(f)
    dflt_vals = json.loads(json.dumps(vals["llm_judge"]), object_hook=lambda d: SimpleNamespace(**d))

class CustomOllamaModel(DeepEvalBaseLLM):
    def __init__(self, model_name : str, url : str = os.getenv("OLLAMA_URL", dflt_vals.ollama_endpoint), *args, **kwargs):
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

class LLMJudgeStrategy(Strategy):
    def __init__(self, name: str = "llm_judge", **kwargs) -> None:
        super().__init__(name=name)
        self.judge_prompt = kwargs.get("judge_prompt", dflt_vals.judge_prompt)
        self.metric_name = kwargs.get("metric_name", dflt_vals.metric_name)
        self.model_name = kwargs.get("model_name", os.getenv("LLM_AS_JUDGE_MODEL"))
        self.base_url = kwargs.get("base_url", os.getenv("OLLAMA_URL"))
        self.prompt = kwargs.get("prompt", dflt_vals.prompt)
        self.system_prompt = kwargs.get("system_prompt", dflt_vals.sys_prompt)
        self.model = CustomOllamaModel(model_name=self.model_name, url=self.base_url)
        self.metric = GEval(
            name= self.metric_name,
            criteria=self.judge_prompt,
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=self.model
        )

        self.logger = get_logger("LLMJudgeStrategy")

        if not self.model_name:
            self.logger.warning("LLM_AS_JUDGE_MODEL is not set in environment.")
        if not self.base_url:
            self.logger.warning("OLLAMA_URL is not set in environment.")

    def evaluate(self, agent_response: str, expected_response: Optional[str]=None):
        self.logger.debug("Evaluating agent response using LLM judge...")
        testcase = LLMTestCase(
            input = self.prompt,
            actual_output=agent_response,
            expected_output=expected_response,
            retrieval_context=[self.system_prompt]
        )
        eval_score = self.metric.measure(testcase)
        self.logger.debug(f"Score: {eval_score}, Reason: {self.model.score_reason}")
        return eval_score
        

# dir_path = os.path.dirname(os.path.realpath(__file__))
# path = os.path.join(dir_path, "data/examples_for_llm_judge.json")
# with open(path, "r") as f:
#     examples = json.load(f)

# for i, ex in enumerate(examples):
#     judge = LLMJudgeStrategy(
#             metric_name="inclusivity",
#             model_name= "qwen2.5:14b", #"mistral:7b-instruct", "llama2:13b", "qwen2.5:14b"
#             prompt=ex['prompt'], 
#             judge_prompt=ex['judge_prompt'], 
#             system_prompt=ex['sys_prompt']
#         )

#     agent_response = ex['agent_resp']
#     expected_response = ex['expected_op']

#     score = judge.evaluate(agent_response, expected_response)
#     print(f"Example {i+1} is given : {score} score.") #The reason is : {judge.model.score_reason}")

# pprint(f"{judge.model.steps}")
# pprint(f"{judge.model.score_reason}")

#/usr/share/ollama/.ollama/models/manifests
    


