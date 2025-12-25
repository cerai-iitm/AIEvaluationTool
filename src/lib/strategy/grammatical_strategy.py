import warnings
import language_tool_python
from typing import Optional
from langdetect import detect
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
import os
from ollama import Client
import json

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("grammatical_strategies")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="grammatical_strategies")

# This module implements grammatical strategies to analyze the agent response.
class GrammaticalStrategy(Strategy):
    def __init__(self, name: str = "grammatical_strategies", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.ollama_url = os.getenv("OLLAMA_URL")

    def grammarCorrector(self, text:str):
        tool = language_tool_python.LanguageTool('en-US')
        result = tool.check(text)
        if not result:
            return text
        else:
            return tool.correct(text)
    
    def get_prompt(self, original:str, corrected:str):
        text = dflt_vals.prompt.format(ori=original, corr=corrected)
        return text
    
    def ollama_connect(self, model_name:str, text:str):
        ollama_client = Client(host=self.ollama_url)
        try:
            """
            We are making a strong assumption that the model we provide will return a 
            proper score for the grammar.
            """
            response = ollama_client.chat(
                model = model_name,
                messages = [
                    {
                        "role" : "user",
                        "content" : f"{text} /nothink",
                    }
                ],
                format="json",
            )
        except Exception as e:
            logger.error(f"Could not communicate with the {model_name}. Make sure the model is downloaded and running.")
            return {}
        try:
            final = response.message.content
            return json.loads(final)
        except:
            return {}
    
    def check_format(self, score_):
        field = "grammar_score"
        field2 = "reason"
        if(isinstance(score_, dict) and field in score_ and field2 in score_ and isinstance(score_.get(field), str) and isinstance(score_.get(field2), str)):
            return True
        return False
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: Optional[str] = None) -> float: #testcase:TestCase, conversation:Conversation):
        logger.info("Evaluating Grammatical Errors...")
        if detect(conversation.agent_response) == "en":
            corrected = self.grammarCorrector(conversation.agent_response)
            prompt = self.get_prompt(conversation.agent_response, corrected)
            resp = self.ollama_connect(dflt_vals.model_name, prompt)
            if(self.check_format(resp)):
                grammar_score = float(resp["grammar_score"])
                response = resp["reason"]
            else:
                grammar_score = 0.0
                response = ""
                logger.error("The response received is not in the specified format.")
            logger.info(f"The grammar consistency score for the given input is : {grammar_score}.")
        else:
            grammar_score = 0.0
            logger.error(f"The identified language is not English. Returning a 0 score.")
        return grammar_score, response
    
# # Test
# strategy = GrammaticalStrategy()
# response = "They is coming home for the cristmas"
# score = strategy.evaluate(response)
# print(f"Grammatical Score: {score}")