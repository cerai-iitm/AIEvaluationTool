import warnings, os
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader
from ddgs import DDGS

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("hallucination")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="hallucination")

class HallucinationStrategy(Strategy):
    def __init__(self, name = "hallucination", **kwargs):
        super().__init__(name, **kwargs)
        pass

    def get_important(self):
        pass
    
    def find_relevant(self):
        pass

    def scrape_(self):
        pass

    def preprocess(self):
        pass

    def vector_store(self):
        pass

    def search_relevant_in_db(self):
        pass
    
    #generate an augmented output based on the prompt by following the previous methods, summarize if required 
    def aug_generate(self):
        pass
    
    # this is the only function that is not a util i think currently
    def compare_with_bot_op(self):
        pass

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        pass

