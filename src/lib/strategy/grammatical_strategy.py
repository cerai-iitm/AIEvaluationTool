import warnings
import language_tool_python
from typing import Optional
from langdetect import detect
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
import spacy

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("grammatical_strategies")

nlp = spacy.load("en_core_web_sm")

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
    
    def dep_parser(self, doc_obj):
        #(head_text, dependency_label, child_text)
        arcs = set()
        for token in doc_obj:
            if token.dep_ != "ROOT":
                head = token.head.text.lower()
                child = token.text.lower()
                dep = token.dep_
                arcs.add((head, dep, child))
        return arcs
    
    def dep_similarity(self, original:str, corrected:str):
        doc_ori, doc_corr = nlp(original), nlp(corrected)
        dep_arc_ori, dep_arc_corr = self.dep_parser(doc_ori), self.dep_parser(doc_corr)
        # for very short sentences there might not be any dependency arcs
        if(len(dep_arc_corr) == 0 and len(dep_arc_ori) == 0):
            return 1.0
        # we want to find the maximum number of changes that leads from original to corrected dependency arcs
        changes = dep_arc_ori.symmetric_difference(dep_arc_corr)
        union = dep_arc_ori.union(dep_arc_corr)
        sim_score = 1 - (len(changes) / len(union))
        return sim_score
    
    def evaluate(self, testcase:TestCase, conversation:Conversation): #agent_response: str, expected_response: Optional[str] = None) -> float: #testcase:TestCase, conversation:Conversation):
        logger.info("Evaluating Grammatical Errors...")
        if detect(conversation.agent_response) == "en":
            corrected = self.grammarCorrector(conversation.agent_response)
            print(corrected)
            grammar_score = round(self.dep_similarity(conversation.agent_response, corrected), 3)
            logger.info(f"The grammar consistency score for the given input is : {grammar_score}.")
        else:
            grammar_score = 0.0
            logger.error(f"The identified language is not English. Returning a 0 score.")
        return grammar_score
    
# # Test
# strategy = GrammaticalStrategy()
# response = "They is coming home for the cristmas"
# score = strategy.evaluate(response)
# print(f"Grammatical Score: {score}")