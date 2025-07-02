import torch
import math
import difflib
import nltk
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer, AutoModelForCausalLM

nltk.download('punkt')

class SarvamModel:
    def __init__(self, model_id="sarvamai/sarvam-2b-v0.5"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        if torch.cuda.is_available():
            print("Using GPU")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.float16, device_map="auto"
            )
        else:
            print("Using CPU")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id, torch_dtype=torch.float32
            ).to("cpu")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def generate(self, prompt, max_new_tokens=1024):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def compute_loss(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with self.tokenizer.as_target_tokenizer():
            labels = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs, labels=labels)
        return outputs.loss.item()


class SentenceEvaluator:
    def __init__(self, model: SarvamModel):
        self.model = model

    def refine(self, text, lang):
        prompt = f"""<|user|>
Correct any grammatical, spelling, or meaning errors in the following sentence and return only the corrected sentence strictly in {lang} and in {lang} script after "Corrected Sentence:".

Sentence: {text}

Respond below only with the corrected sentence in {lang}:

<|assistant|>
Corrected Sentence:
"""
        output = self.model.generate(prompt)
        try:
            corrected = output.split("Corrected Sentence:")[-1].strip()
        except:
            corrected = output.strip()
        return corrected

    def count_corrections(self, original, corrected):
        original_words = original.split()
        corrected_words = corrected.split()
        diff = difflib.SequenceMatcher(None, original_words, corrected_words)
        changes = sum(1 for tag, *_ in diff.get_opcodes() if tag != 'equal')
        return changes, len(original_words)

    def fluency_score(self, text):
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return 1.0
        losses = []
        for i in range(len(sentences) - 1):
            context = sentences[i].strip()
            continuation = sentences[i + 1].strip()
            prompt = f"{context} {continuation}"
            loss = self.model.compute_loss(prompt)
            losses.append(loss)
        avg_loss = sum(losses) / len(losses)
        return round(math.exp(-avg_loss), 4)


class EvaluationManager:
    def __init__(self, evaluator: SentenceEvaluator):
        self.evaluator = evaluator

    def evaluate_samples(self, samples):
        results = []
        for text, lang in samples:
            corrected = self.evaluator.refine(text, lang)
            corrections, total_words = self.evaluator.count_corrections(text, corrected)
            grammar_score = round(1.0 - (corrections / total_words), 2) if total_words > 0 else 0.0
            fluency = self.evaluator.fluency_score(corrected)
            results.append({
                "language": lang,
                "original": text,
                "corrected": corrected,
                "grammar_score": grammar_score,
                "fluency_score": fluency,
                "corrections": corrections,
                "total_words": total_words
            })
        return results

    def print_results(self, results):
        for item in results:
            print(f"{item['language']:<10} | Grammar: {item['grammar_score']} | Fluency: {item['fluency_score']} | Corrections: {item['corrections']}")
            print(f"Original : {item['original']}")
            print(f"Corrected: {item['corrected']}")
            print("-" * 100)