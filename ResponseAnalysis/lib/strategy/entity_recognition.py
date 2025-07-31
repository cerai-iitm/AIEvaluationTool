import re
import json
import warnings
from strategy_base import Strategy
from logger import get_logger
from typing import List, Tuple

logger = get_logger("entity_recognition")

warnings.filterwarnings("ignore")

# This module compute Entity Recognition Accuracy (NER detection) of the AI agents
class EntityRecognition(Strategy):
    def __init__(self, name: str = "entity_recognition", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

    def extract_entity_pairs(self, text: str) -> List[Tuple[str, str]]:
        """
        Extracts (entity, ner_tag) pairs from loosely structured dict-like strings.
        """
        text = text.replace("```", "").strip()

        pattern = re.compile(
            r"""\{\s*['"]?entity['"]?\s*:\s*['"]?([^,'"}\n]+)['"]?\s*,\s*['"]?ner_tag['"]?\s*:\s*['"]?([^,'"}\n]+)['"]?\s*\}""",
            re.IGNORECASE
        )
        matches = pattern.findall(text)

        return [(entity.strip().lower(), tag.strip().upper()) for entity, tag in matches]

    def ner_recognition(self, expected_str: str, response_str: str) -> float:
        """
        Computes and returns only the F1 score between expected and predicted entity-tag strings.
        """
        expected_pairs = set(self.extract_entity_pairs(expected_str))
        predicted_pairs = set(self.extract_entity_pairs(response_str))

        # print(f"Expected pairs: {expected_pairs} and Predicted pairs: {predicted_pairs}")

        tp = len(expected_pairs & predicted_pairs)
        fp = len(predicted_pairs - expected_pairs)
        fn = len(expected_pairs - predicted_pairs)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return round(f1, 4)

    def evaluate(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates the agent response against expected and returns only the F1 score.
        """
        logger.info(f"Result: {self.ner_recognition(expected_str=expected_response, response_str=agent_response)}")
        return self.ner_recognition(expected_str=expected_response, response_str=agent_response)

# Example usage
# expected_response = """
# {'entity' :  weeder ,  'ner_tag' :  TOOL },  { 'entity' :  floods ,  'ner_tag' :  DISASTER},  { 'entity' :  dibbler ,  'ner_tag' :  TOOL },  { 'entity' :  saplings ,  'ner_tag' :  PLANT_STAGE },  { 'entity' :  cutworm ,  'ner_tag' :  PEST },  { 'entity' :  beetles ,  'ner_tag' :  PEST }
# """
# # expected_response ="""
# # entity': 'weeder', 'ner_tag': 'Tool'}\n{'entity': 'dibbler', 'ner_tag': 'Tool'}\n{'entity': 'seedlings', 'ner_tag': 'Crop'}\n{'entity': 'cutworm', 'ner_tag': 'Pest'}\n{'entity': 'beetles', 'ner_tag': 'Pest'}
# # """
# agent_response = """
# Here are the agricultural entities extracted from the text: {'entity': 'weeder', 'ner_tag': 'Tool'}\n{'entity': 'dibbler', 'ner_tag': 'Tool'}\n{'entity': 'seedlings', 'ner_tag': 'Crop'}\n{'entity': 'cutworm', 'ner_tag': 'Pest'}\n{'entity': 'beetles', 'ner_tag': 'Pest'}
# """

# ner_eval = EntityRecognition()
# ner_recogition_score = ner_eval.evaluate(agent_response, expected_response)
# print("Entity Recogntion Accuracy:", ner_recogition_score)
# Entity Recognition Accuracy working
