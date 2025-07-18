import re
import json
import warnings
from strategy_base import Strategy
from logger import get_logger

logger = get_logger("entity_recognition")

warnings.filterwarnings("ignore")

# This module compute Entity Recognition Accuracy (NER detection) of the AI agents
class EntityRecognition(Strategy):
    def __init__(self, name: str = "entity_recognition", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

    def extract_entity_pairs(self, text: str):
        """
        Extracts (entity, ner_tag) pairs using regex from the given text.

        :param text: String containing entity-tag objects like {'entity': 'wheat', 'ner_tag': 'CROP'}
        :return: List of normalized (entity, tag) tuples
        """
        pairs = []

        # Clean 
        text = text.replace("```", "").strip().strip(',')

        # Try parsing structured JSON block if present
        try:
            # Try extracting list of dicts inside square brackets
            list_match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
            if list_match:
                data = json.loads(list_match.group(0))
            else:
                # Attempt to wrap plain dicts into a list and parse
                data = json.loads(f"[{text}]")
            
            for item in data:
                if isinstance(item, dict) and "entity" in item and "ner_tag" in item:
                    pairs.append((item["entity"].strip().lower(), item["ner_tag"].strip().upper()))
            return pairs
        except Exception:
            pass  # Fallback to regex if parsing fails

        # Fallback regex pattern (less strict, accepts mixed quotes)
        pattern = re.compile(r"""\{\s*['"]entity['"]\s*:\s*['"](.*?)['"]\s*,\s*['"]ner_tag['"]\s*:\s*['"](.*?)['"]\s*\}""", re.DOTALL)
        matches = pattern.findall(text)
        return [(ent.strip().lower(), tag.strip().upper()) for ent, tag in matches]

    def ner_recognition(self, expected_str: str, response_str: str) -> dict:
        """
        Evaluate NER F1-score between expected and predicted entity-tag strings.

        :param expected_str: Raw string with expected entities and tags.
        :param response_str: Raw string with predicted entities and tags.
        :return: Dict with precision, recall, f1_score and detailed stats.
        """
        expected_pairs = set(self.extract_entity_pairs(expected_str))
        predicted_pairs = set(self.extract_entity_pairs(response_str))

        tp = len(expected_pairs & predicted_pairs)
        fp = len(predicted_pairs - expected_pairs)
        fn = len(expected_pairs - predicted_pairs)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        logger.info(f"F1 Score: {round(f1, 4)}")
        return round(f1, 4)

    def evaluate(self, agent_response: str, expected_response: str) -> dict:
        """
        Public interface to evaluate a single agent response against expected response.

        :param agent_response: String containing model output with entity-tag pairs.
        :param expected_response: String containing expected entity-tag pairs.
        :return: Evaluation metrics as dict.
        """
        return self.ner_recognition(expected_response, agent_response)


# Example usage
# expected_response = """
# {'entity': 'wheat', 'ner_tag': 'CROP'}, {'entity': 'punjab', 'ner_tag': 'LOCATION'}
# """

# agent_response = """
# Here is the extracted entities: {'entity': 'wheat', 'ner_tag': 'CROP'}, {'entity': 'punjab', 'ner_tag': 'LOCATION'}, {'entity': 'india', 'ner_tag': 'COUNTRY'}
# """

# ner_eval = EntityRecognition()
# ner_recogition_score = ner_eval.evaluate(agent_response, expected_response)
# print("Entity Recogntion Accuracy:", ner_recogition_score)
# Entity Recognition Accuracy working
