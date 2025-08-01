from strategy_base import Strategy
from typing import Optional, Dict
import re
import asyncio
from utils import detect_text, google_lang_translate
from logger import get_logger

logger = get_logger("hallucination")

class HallucinationStrategy(Strategy):
    """
    Strategy for evaluating hallucination metrics across different task types.
    Supports: QA, summarization, dialogue, and multiple-choice tasks.
    """

    def __init__(self, name: str = "hallucination", **kwargs) -> None:
        """
        Initializes the HallucinationStrategy.

        Parameters:
        - name (str): Name of the strategy.
        - kwargs: Additional parameters.
        """
        super().__init__(name, kwargs=kwargs)
        self.source_type = kwargs.get("source_type", "haluqa")  # Default source type

    def _extract_prediction(self, response: str, source_type: str) -> str:
        """
        Extracts the predicted answer from the agent response based on the source type.

        Parameters:
        - response (str): Agent's response text.
        - source_type (str): Type of source (haluqa, halusumm, haludial, mc).

        Returns:
        - str: Extracted prediction (yes/no/option/na).
        """
        response = response.strip().lower()

        if source_type in ["haluqa", "halusumm", "haludial"]:
            if response.startswith("yes"):
                return "yes"
            elif response.startswith("no"):
                return "no"
            else:
                return "na"

        elif source_type == "mc":
            response_clean = re.sub(r"[^a-zA-Z]", "", response.split()[0].upper())
            if response_clean in ["A", "B", "C", "D"]:
                return response_clean
            else:
                return "na"

        return "na"

    def _translate_if_needed(self, text: str) -> str:
        """
        Translates the given text to English if it is in another language.

        Parameters:
        - text (str): Text to be translated.

        Returns:
        - str: Translated text in English.
        """
        lang = asyncio.run(detect_text(text))
        if lang == "en":
            return text
        else:
            translated_text = asyncio.run(google_lang_translate(text))
            return translated_text

    def halu_qa(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates hallucination for a single QA task.

        Parameters:
        - agent_response (str): Agent-generated response.
        - expected_response (str): Expected ground-truth answer.

        Returns:
        - float: 1.0 if correct, 0.0 if incorrect.
        """
        logger.info("Evaluating Hallucination - QA Task")
        translated_resp = self._translate_if_needed(agent_response)
        prediction = self._extract_prediction(translated_resp, "haluqa")
        score = 1.0 if prediction == expected_response.lower() else 0.0
        logger.info(f"Agent Response: {agent_response} | Prediction: {prediction} | Expected: {expected_response} | Score: {score}")
        return score

    def halu_summ(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates hallucination for a single Summarization task.

        Parameters:
        - agent_response (str): Agent-generated summary.
        - expected_response (str): Expected ground-truth summary.

        Returns:
        - float: 1.0 if correct, 0.0 if incorrect.
        """
        logger.info("Evaluating Hallucination - Summarization Task")
        translated_resp = self._translate_if_needed(agent_response)
        prediction = self._extract_prediction(translated_resp, "halusumm")
        score = 1.0 if prediction == expected_response.lower() else 0.0
        logger.info(f"Agent Response: {agent_response} | Prediction: {prediction} | Expected: {expected_response} | Score: {score}")
        return score

    def halu_dial(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates hallucination for a single Dialogue task.

        Parameters:
        - agent_response (str): Agent-generated dialogue response.
        - expected_response (str): Expected ground-truth response.

        Returns:
        - float: 1.0 if correct, 0.0 if incorrect.
        """
        logger.info("Evaluating Hallucination - Dialogue Task")
        translated_resp = self._translate_if_needed(agent_response)
        prediction = self._extract_prediction(translated_resp, "haludial")
        score = 1.0 if prediction == expected_response.lower() else 0.0
        logger.info(f"Agent Response: {agent_response} | Prediction: {prediction} | Expected: {expected_response} | Score: {score}")
        return score

    def mc(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates hallucination for a single Multiple-Choice task.

        Parameters:
        - agent_response (str): Agent-generated multiple-choice answer.
        - expected_response (str): Expected correct option (A, B, C, D).

        Returns:
        - float: 1.0 if correct, 0.0 if incorrect.
        """
        logger.info("Evaluating Hallucination - Multiple Choice Task")
        translated_resp = self._translate_if_needed(agent_response)
        prediction = self._extract_prediction(translated_resp, "mc")
        score = 1.0 if prediction == expected_response.upper() else 0.0
        logger.info(f"Agent Response: {agent_response} | Prediction: {prediction} | Expected: {expected_response} | Score: {score}")
        return score

    def evaluate(self, agent_response: str, expected_response: str) -> float:
        """
        Unified evaluation entry point for all hallucination tasks.

        Parameters:
        - agent_response (str): Agent's response.
        - expected_response (str): Expected ground-truth response.
        - source_type (str): Type of task ('haluqa', 'halusumm', 'haludial', 'mc').

        Returns:
        - float: Score (1.0 for correct, 0.0 for incorrect).
        """
        logger.info(f"Evaluating Hallucination for source type: {self.source_type}")
        if self.source_type == "haluqa":
            return self.halu_qa(agent_response, expected_response)
        elif self.source_type == "halusumm":
            return self.halu_summ(agent_response, expected_response)
        elif self.source_type == "haludial":
            return self.halu_dial(agent_response, expected_response)
        elif self.source_type == "mc":
            return self.mc(agent_response, expected_response)
        else:
            logger.warning(f"Unsupported source type: {self.source_type}")
            return 0.0
   
#test
'''
from hallucination import HallucinationStrategy

def run_tests():
    hallu = HallucinationStrategy()

    agent_response = "Yes, that is correct."
    expected_response = "yes"
    source_type = "halu_qa"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 1 (QA - Correct): Score = {score}") 

    agent_response = "No, that is not the case."
    expected_response = "yes"
    source_type = "halu_summ"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 2 (Summarization - Incorrect): Score = {score}")  

    agent_response = "No, I don't agree."
    expected_response = "no"
    source_type = "halu_dial"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 3 (Dialogue - Correct): Score = {score}")  

    agent_response = "A. The answer is option A."
    expected_response = "A"
    source_type = "mc"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 4 (MC - Correct): Score = {score}")  

    agent_response = "B. I think it's B."
    expected_response = "C"
    source_type = "mc"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 5 (MC - Incorrect): Score = {score}")

    agent_response = "This is a random response."
    expected_response = "yes"
    source_type = "unsupported_type"
    score = hallu.evaluate(agent_response, expected_response, source_type)
    print(f"Test 6 (Unsupported Source Type): Score = {score}")

if __name__ == "__main__":
    run_tests()
'''