from strategy_base import Strategy
from typing import Optional, List, Dict
import re
import logging
import asyncio
from utils import detect_text, google_lang_translate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("analyzer_log.log")
    ]
)

logger = logging.getLogger(__name__)

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

    def _extract_prediction(self, response: str, source_type: str) -> str:
        """
        Extracts the predicted answer from the agent response based on the source type.

        Parameters:
        - response (str): Agent's response text.
        - source_type (str): Type of source (halu_qa, halu_summ, halu_dial, mc).

        Returns:
        - str: Extracted prediction (yes/no/option/na).
        """
        response = response.strip().lower()

        if source_type in ["halu_qa", "halu_summ", "halu_dial"]:
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

    def halu_qa(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        """
        Evaluates hallucination for QA tasks.

        Parameters:
        - agent_responses (List[str]): List of agent-generated responses.
        - expected_responses (List[str]): List of expected ground-truth answers.

        Returns:
        - float: Average accuracy score for hallucination detection in QA.
        """
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_qa")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def halu_summ(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        """
        Evaluates hallucination for summarization tasks.

        Parameters:
        - agent_responses (List[str]): List of agent-generated summaries.
        - expected_responses (List[str]): List of expected ground-truth summaries.

        Returns:
        - float: Average accuracy score for hallucination detection in summarization.
        """
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_summ")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def halu_dial(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        """
        Evaluates hallucination for dialogue tasks.

        Parameters:
        - agent_responses (List[str]): List of agent-generated dialogue responses.
        - expected_responses (List[str]): List of expected ground-truth responses.

        Returns:
        - float: Average accuracy score for hallucination detection in dialogue.
        """
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_dial")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def mc(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        """
        Evaluates hallucination for multiple-choice tasks.

        Parameters:
        - agent_responses (List[str]): List of agent-generated multiple-choice answers.
        - expected_responses (List[str]): List of expected correct options (A, B, C, D).

        Returns:
        - float: Average accuracy score for hallucination detection in multiple-choice tasks.
        """
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "mc")
            score = 1.0 if prediction == expected_resp.upper() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def evaluate(self, data_points: List[Dict]) -> Dict[str, float]:
        """
        Evaluates all supported hallucination tasks and computes accuracy for each.

        Parameters:
        - data_points (List[Dict]): List of test cases containing agent response, expected response, and source type.

        Returns:
        - Dict[str, float]: Dictionary containing average scores for each hallucination type.
        """
        grouped_data = {"halu_qa": [], "halu_summ": [], "halu_dial": [], "mc": []}

        for dp in data_points:
            source = dp["source"]
            if source in grouped_data:
                grouped_data[source].append(dp)

        results = {}

        if grouped_data["halu_qa"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["halu_qa"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["halu_qa"]]
            results["halu_qa"] = self.halu_qa(agent_responses, expected_responses)

        if grouped_data["halu_summ"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["halu_summ"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["halu_summ"]]
            results["halu_summ"] = self.halu_summ(agent_responses, expected_responses)

        if grouped_data["halu_dial"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["halu_dial"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["halu_dial"]]
            results["halu_dial"] = self.halu_dial(agent_responses, expected_responses)

        if grouped_data["mc"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["mc"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["mc"]]
            results["mc"] = self.mc(agent_responses, expected_responses)

        return results
   
#test
'''
from hallucination import HallucinationStrategy

def test_hallucination_strategy_multilingual():
    strategy = HallucinationStrategy()

    test_data = [
        # halu_qa
        {"source": "halu_qa", "agent_response": "Yes", "expected_response": "yes"},
        {"source": "halu_qa", "agent_response": "हाँ", "expected_response": "yes"},   
        {"source": "halu_qa", "agent_response": "No", "expected_response": "no"},   
        {"source": "halu_qa", "agent_response": "नहीं", "expected_response": "no"},  

        # halu_summ
        {"source": "halu_summ", "agent_response": "No", "expected_response": "no"},   
        {"source": "halu_summ", "agent_response": "हाँ", "expected_response": "yes"},  
        {"source": "halu_summ", "agent_response": "No", "expected_response": "yes"},

        # halu_dial
        {"source": "halu_dial", "agent_response": "Yes", "expected_response": "yes"}, 
        {"source": "halu_dial", "agent_response": "नहीं", "expected_response": "no"},   

        # mc
        {"source": "mc", "agent_response": "A", "expected_response": "A"},            
        {"source": "mc", "agent_response": "बी", "expected_response": "B"},            
    ]
    results = strategy.evaluate(test_data)

    print("Hallucination Strategy Multilingual Test Results:")
    for metric, score in results.items():
        print(f"{metric}: Average Score = {score:.2f}")

if __name__ == "__main__":
    test_hallucination_strategy_multilingual()
'''