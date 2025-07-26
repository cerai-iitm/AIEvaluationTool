import requests
import difflib
import nltk
from strategy_base import Strategy
from typing import Optional
import os 
from dotenv import load_dotenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from logger import get_logger

logger = get_logger("indian_lang_grammatical_check")

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
        prompt = f'''<|user|>
Correct any grammatical, spelling, or meaning errors in the following sentence and return only the corrected sentence strictly in {lang} and in {lang} script after "Corrected Sentence:".

Sentence: {text}

Respond below only with the corrected sentence in {lang}:

<|assistant|>
Corrected Sentence:
'''
        output = requests.post(f"{self.gpu_url}/generate",params={"prompt": prompt})
        data = output.json()
        corrected = data.get("generated")
        return corrected

    def count_corrections(self, original, corrected):
        original_words = original
        corrected_words = corrected
        diff = difflib.SequenceMatcher(None, original_words, corrected_words)
        changes = sum(1 for tag, *_ in diff.get_opcodes() if tag != 'equal')
        return changes, len(original_words)

    def evaluate(self, agent_response: str, expected_response: Optional[str]=None) -> float:
        corrected = self.check_grammar(agent_response, lang="Hindi")
        corrections, total_words = self.count_corrections(agent_response, corrected)
        grammar_score = round(1.0 - (corrections / total_words), 2) if total_words > 0 else 0.0
        return grammar_score

# if __name__ == "__main__":
#     checker = IndianLangGrammaticalCheck()
#     test_sentence = "यह एक गलत वाक्य है।"
#     score = checker.evaluate(test_sentence)
#     print(f"Grammar score for test sentence: {score}")