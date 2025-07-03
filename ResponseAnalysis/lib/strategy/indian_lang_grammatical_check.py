import torch
import math
import difflib
import nltk
from .utils import SarvamModel
from .strategy_base import Strategy
nltk.download('punkt')

class IndianLangGrammaticalCheck(Strategy):
    def __init__(self, model=None, tokenizer=None, name="indian_lang_grammatical", **kwargs):
        super().__init__(name, kwargs=kwargs)
        self.model = SarvamModel()
        self.tokenizer = tokenizer

    def check_grammar(self, text: str, lang: str) -> str:
        prompt = f"""<|user|>
Correct any grammatical, spelling, or meaning errors in the following sentence and return only the corrected sentence strictly in {lang} and in {lang} script after "Corrected Sentence:".

Sentence: {text}

Respond below only with the corrected sentence in {lang}:

<|assistant|>
Corrected Sentence:
"""
        # You may want to use your model's generate method here, or adapt as needed
        if self.model is not None and hasattr(self.model, 'generate'):
            output = self.model.generate(prompt)
        else:
            output = text  # fallback: return input if no model
        try:
            corrected = output.split("Corrected Sentence:")[-1].strip()
        except Exception:
            corrected = output.strip()
        return corrected

    def count_corrections(self, original, corrected):
        original_words = original.split()
        corrected_words = corrected.split()
        diff = difflib.SequenceMatcher(None, original_words, corrected_words)
        changes = sum(1 for tag, *_ in diff.get_opcodes() if tag != 'equal')
        return changes, len(original_words)

class EvaluationManager:
    def __init__(self, evaluator: IndianLangGrammaticalCheck):
        self.evaluator = evaluator

    def evaluate(self, samples):
        results = []
        for text, lang in samples:
            corrected = self.evaluator.check_grammar(text, lang)
            corrections, total_words = self.evaluator.count_corrections(text, corrected)
            grammar_score = round(1.0 - (corrections / total_words), 2) if total_words > 0 else 0.0
            results.append({
                "language": lang,
                "original": text,
                "grammar_score": grammar_score
            })
        return results

    def print_results(self, results):
        for item in results:
            print(f"{item['language']:<10} | Grammar: {item['grammar_score']}")
            print(f"Original : {item['original']}")