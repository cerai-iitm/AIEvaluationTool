import requests
import nltk
import difflib
import os 
import warnings
from typing import Optional
import json
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("indian_lang_grammatical_check")

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download('punkt')

class IndianLangGrammaticalCheck(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_grammatical_check", **kwargs):
        super().__init__(name, **kwargs)
        self.gpu_url=os.getenv("GPU_URL")

        if not self.gpu_url:
            logger.warning("GPU_URL is not set in environment.")
        else:
            logger.info("GPU_URL is loaded from environment.")

    def check_grammar(self, text: str, lang: str) -> str:
#         prompt = f'''<|user|>
# Correct any grammatical, spelling, or meaning errors in the following sentence and return only the corrected sentence strictly in {lang} and in {lang} script after "Corrected Sentence:".

# Sentence: {text}

# Respond below only with the corrected sentence in {lang}:

# <|assistant|>
# Corrected Sentence:
# '''    
        prompt = text
        output = requests.post(f"{self.gpu_url}/generate",params={"prompt": prompt})
        data = output.json()
        corrected = data.get("generated")
        return corrected

    def count_corrections(self, original, corrected):
        original_words = original
        corrected_words = corrected
        print(corrected_words)
        def translate(agent_response:str):
            return json.loads(requests.post(f"{self.gpu_url}/translate", params={"input_text" : agent_response, "target_language" : "English"}).content.decode('utf-8'))
        print(translate("என் வயிறு ரொம்ப வலிக்குது, அதனால இன்னிக்கு ஸ்கூலுக்கு போறேன்."))
        diff = difflib.SequenceMatcher(None, original_words, corrected_words)
        changes = sum(1 for tag, *_ in diff.get_opcodes() if tag != 'equal')
        return changes, len(original_words)

    def evaluate(self, agent_response: str, expected_response: Optional[str]=None) -> float:#testcase:TestCase, conversation:Conversation):#agent_response: str, expected_response: Optional[str]=None) -> float:
        corrected = self.check_grammar(agent_response, lang="Hindi")#conversation.agent_response, lang="Hindi")
        corrections, total_words = self.count_corrections(agent_response, corrected)#conversation.agent_response, corrected)
        grammar_score = round(1.0 - (corrections / total_words), 2) if total_words > 0 else 0.0
        return grammar_score

if __name__ == "__main__":
    checker = IndianLangGrammaticalCheck()
    test_sentence = '''### Instruction : 
    Give me the grammatically correct sentence for the input below in the same language as the input.   
    
    ### Input:
    वो लोग कल मेरे घर आने वाला थे लेकिन मैं नहीं जानता हूँ कि क्यों वो सब नहीं आया था और मैं पूरा टाइम इंतज़ार करता रहा था हूँ.
    
    ### Response:'''

    score = checker.evaluate(test_sentence)
    print(f"Grammar score for test sentence: {score}")