import warnings
import os
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from .utils_new import FileLoader, CustomOllamaModel
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger

# sys.path.append(os.path.dirname(__file__) + '/..')
warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("llm_judge")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="llm_judge")

class LLMJudgeStrategy(Strategy):
    def __init__(self, name: str = "llm_judge", **kwargs) -> None:
        super().__init__(name=name)
        
        self.metric_name = kwargs.get("metric_name", dflt_vals.metric_name)
        self.model_name = os.getenv("LLM_AS_JUDGE_MODEL")
        self.base_url = os.getenv("OLLAMA_URL")
        self.model = CustomOllamaModel(model_name=self.model_name, url=self.base_url)
        self.eval_type = name.split("_")[-1] if len(name.split("_")) > 2 else dflt_vals.eval_type
        
        self.judge_prompt = dflt_vals.judge_prompt
        self.system_prompt = dflt_vals.sys_prompt
        self.prompt = dflt_vals.prompt

        if not self.model_name:
            logger.warning("LLM_AS_JUDGE_MODEL is not set in environment.")
        if not self.base_url:
            logger.warning("OLLAMA_URL is not set in environment.")

    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: Optional[str]=None
        logger.debug("Evaluating agent response using LLM judge...")
        # metric is defined here instead of init because if multiple testcases belonging to different metrics are grouped together 
        # for this strategy, the judge prompt will change. So we define the metric here right before executing the testcase.
        self.metric = GEval(
            name= self.metric_name,
            criteria= testcase.judge_prompt.prompt if testcase.judge_prompt.prompt else self.judge_prompt,
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
            model=self.model
        )
        to_evaluate = LLMTestCase(
            input = testcase.prompt.user_prompt if testcase.prompt.user_prompt else self.prompt,
            actual_output=conversation.agent_response,
            expected_output=testcase.response.response_text,
            retrieval_context=[testcase.prompt.system_prompt if testcase.prompt.system_prompt else self.system_prompt]
        )
        # print(f"JUDGE_PROMPT : {testcase.judge_prompt.prompt}, SYSTEM_PROMPT : {testcase.prompt.system_prompt}, PROMPT : {testcase.prompt.user_prompt}")

        eval_score = self.metric.measure(to_evaluate)
        final_score = eval_score if self.eval_type == "positive" else (1 - eval_score)
        logger.info(f"Score: {final_score}, Reason: {self.model.score_reason}")
        return final_score
        

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
    


