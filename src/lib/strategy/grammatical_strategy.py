import warnings
import language_tool_python
from typing import Optional
from langdetect import detect
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect
import os
import numpy as np

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("grammatical_strategies")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="grammatical_strategies")

# This module implements grammatical strategies to analyze the agent response.
class GrammaticalStrategy(Strategy):
    def __init__(self, name: str = "grammatical_strategies", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

    def grammarCorrector(self, text:str):
        tool = language_tool_python.LanguageTool('en-US')
        result = tool.check(text)
        if not result:
            return text
        else:
            return tool.correct(text)
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: Optional[str] = None) -> float: #testcase:TestCase, conversation:Conversation):
        logger.info("Evaluating Grammatical Errors...")
        grammar_score = 0.0
        reason = ""
        if detect(conversation.agent_response) == "en":
            corrected = self.grammarCorrector(conversation.agent_response)
            prompt = dflt_vals.prompt.format(ori=conversation.agent_response, corr=corrected)
            resp = OllamaConnect.prompt_model(prompt, dflt_vals.reqd_flds)
            if len(resp) > 0:
                grammar_score = float(np.mean([float(r["grammar_score"]) for r in resp]))
                reasons = [r["reason"] for r in resp]
                for i, r in enumerate(reasons):
                    if i == 0:
                        reason += f"Reason {i} : {r}"
                    else:
                        reason += f"\n\n Reason {i} : {r}"
            else:
                logger.info("Did not receive a proper response from the models. Returning a 0 score.")
            logger.info(f"The grammar consistency score for the given input is : {grammar_score}.")
        else:
            logger.error(f"The identified language is not English. Returning a 0 score.")
        return grammar_score, reason
    
# # Test
# strategy = GrammaticalStrategy()
# response = "They is coming home for the cristmas"
# score = strategy.evaluate(response)
# print(f"Grammatical Score: {score}")