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
    def __init__(self, name: str = "hallucination", **kwargs) -> None:
        """
        Strategy for evaluating hallucination based on different source types.
        """
        super().__init__(name, kwargs=kwargs)

    def _extract_prediction(self, response: str, source_type: str) -> str:
        """
        Extracts the predicted answer from the agent response based on the source type.
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
        Translates the text to English if the detected language is not English.
        """
        lang = asyncio.run(detect_text(text))
        if lang == "en":
            return text
        else:
            translated_text = asyncio.run(google_lang_translate(text))
            return translated_text

    def evaluate_halu_qa(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_qa")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def evaluate_halu_summ(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_summ")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def evaluate_halu_dial(self, agent_responses: List[str], expected_responses: List[str]) -> float:
        scores = []
        for agent_resp, expected_resp in zip(agent_responses, expected_responses):
            translated_resp = self._translate_if_needed(agent_resp)
            prediction = self._extract_prediction(translated_resp, "halu_dial")
            score = 1.0 if prediction == expected_resp.lower() else 0.0
            scores.append(score)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score

    def evaluate_mc(self, agent_responses: List[str], expected_responses: List[str]) -> float:
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
        Evaluates all hallucination metrics and returns the average score for each.
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
            results["halu_qa"] = self.evaluate_halu_qa(agent_responses, expected_responses)

        if grouped_data["halu_summ"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["halu_summ"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["halu_summ"]]
            results["halu_summ"] = self.evaluate_halu_summ(agent_responses, expected_responses)

        if grouped_data["halu_dial"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["halu_dial"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["halu_dial"]]
            results["halu_dial"] = self.evaluate_halu_dial(agent_responses, expected_responses)

        if grouped_data["mc"]:
            agent_responses = [dp["agent_response"] for dp in grouped_data["mc"]]
            expected_responses = [dp["expected_response"] for dp in grouped_data["mc"]]
            results["mc"] = self.evaluate_mc(agent_responses, expected_responses)

        return results

from hallucination import HallucinationStrategy

def test_hallucination_strategy_multilingual():
    strategy = HallucinationStrategy()

    # Prepare 10 test samples covering all sources and mixed languages
    test_data = [
        # halu_qa
        {"source": "halu_qa", "agent_response": "Yes", "expected_response": "yes"},  # English
        {"source": "halu_qa", "agent_response": "हाँ", "expected_response": "yes"},   # Hindi (will be translated)
        {"source": "halu_qa", "agent_response": "No", "expected_response": "no"},     # English
        {"source": "halu_qa", "agent_response": "नहीं", "expected_response": "no"},   # Hindi (will be translated)

        # halu_summ
        {"source": "halu_summ", "agent_response": "No", "expected_response": "no"},   # English
        {"source": "halu_summ", "agent_response": "हाँ", "expected_response": "yes"},  # Hindi
        {"source": "halu_summ", "agent_response": "No", "expected_response": "yes"},  # Incorrect

        # halu_dial
        {"source": "halu_dial", "agent_response": "Yes", "expected_response": "yes"},  # English
        {"source": "halu_dial", "agent_response": "नहीं", "expected_response": "no"},   # Hindi

        # mc
        {"source": "mc", "agent_response": "A", "expected_response": "A"},            # English
        {"source": "mc", "agent_response": "बी", "expected_response": "B"},            # Hindi (बी = B) - this should ideally fail unless you handle Hindi options specifically
    ]

    # Run evaluation
    results = strategy.evaluate(test_data)

    # Print results
    print("Hallucination Strategy Multilingual Test Results:")
    for metric, score in results.items():
        print(f"{metric}: Average Score = {score:.2f}")

if __name__ == "__main__":
    test_hallucination_strategy_multilingual()
