import json
import re
import logging
import warnings
from strategy_base import Strategy

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  
        logging.FileHandler("analyzer_log.log")  
    ]
)

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore")

# this module compute Entity Recognition Accuracy (NER detection) of the AI agents
class EntityRecognition(Strategy):
    def __init__(self, name: str = "entity_recognition", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)

    def load_json(filepath):
        """
        Load a JSON file from the specified filepath.
        :param filepath (str) - Path to the JSON file.
        returns: dict or list - Parsed JSON data.
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    def extract_entities_from_response(response_text):
        """
        Extract entity-tag pairs from a model's response using regex pattern matching.
        :param response_text (str) - The raw text response from the model.
        returns List[Tuple[str, str]] - A list of (entity, NER tag) tuples with normalized casing.
        """
        pattern = re.compile(r"\{['\"]entity['\"]:\s*['\"](.*?)['\"],\s*['\"]ner_tag['\"]:\s*['\"](.*?)['\"]\}")
        return [(m[0].strip().lower(), m[1].strip().upper()) for m in pattern.findall(response_text)]

    def evaluate(self, expected_data_list, response_data_list) -> float:
        """
        Evaluate model responses against expected entity-tag outputs using precision, recall, and F1-score.
        :param expected_data_list (List[Dict]) - Ground truth data. Each item must contain:
                - 'PROMPT_ID': str
                - 'EXPECTED_OUTPUT': List[{'entity': str, 'ner_tag': str}]
        :param response_data_list (List[Dict]) - Model output data. Each item must contain:
                - 'prompt_id': str
                - 'response': str (textual model output)
        returns float - The average (mean) F1-score across all prompt-response pairs.
        """
        results = []
        f1_scores = []

        for expected_entry in expected_data_list:
            prompt_id = expected_entry['PROMPT_ID']
            expected_pairs = set(
                (item['entity'].strip().lower(), item['ner_tag'].strip().upper()) 
                for item in expected_entry['EXPECTED_OUTPUT']
            )

            # Match response by prompt_id
            matching_response = next(
                (r for r in response_data_list if r['prompt_id'].strip().lower() == prompt_id.strip().lower()),
                None
            )

            if not matching_response:
                results.append({
                    "prompt_id": prompt_id,
                    "error": "No matching response found."
                })
                continue

            predicted_pairs = set(self.extract_entities_from_response(matching_response['response']))

            tp = len(expected_pairs & predicted_pairs)
            fp = len(predicted_pairs - expected_pairs)
            fn = len(expected_pairs - predicted_pairs)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)

            results.append({
                "prompt_id": prompt_id,
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4)
            })

        # Compute mean F1-score
        mean_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        return round(mean_f1, 4)

# # Example usage
# expected_list = load_json("Data/ground_truth_agriculture_ner.json")  # List of expected entries
# response_list = load_json("Data/responses.json")  # List of responses

# results = evaluate(expected_list, response_list)
# print("Entity Detection Accuray (F1-Score):", results)
