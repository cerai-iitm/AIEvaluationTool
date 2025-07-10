from strategy_base import Strategy
from typing import Optional
import logging
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from nltk.translate.meteor_score import meteor_score
import evaluate
import warnings
from sentence_transformers.util import cos_sim
from evaluate import load
from utils import BARTScorer
from sentence_transformers import SentenceTransformer

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
# This module implements a similarity matching strategy for evaluating agent responses.
# It uses various metrics such as BERT, cosine, and Jaccard similarity to assess the quality of responses.
class SimilarityMatchStrategy(Strategy):
    def __init__(self, name: str = "similarity_match", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        # Initialize the metric name for similarity matching
        # `metric_name` can be "bert_similarity", "cosine_similarity", or "rouge_similarity", "meteor_similarity", "bleu_similarity", "bart_score_similarity"
        self.__metric_name = kwargs.get("metric_name")
        #self.embedding_model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v1')

    def bleu_score_metric(self, predictions, references):
        """
        Calculates the BLEU score between predicted and reference texts.
        Parameters:
        - predictions (list of str): List of predicted output sentences.
        - references (list of str): List of reference (ground truth) sentences.

        Prints:
        - Average BLEU Score (%)
        """
        logger.info("Starting bleu_score_metric evaluation strategy")
        try:
            pred_tokens = predictions.split()
            ref_tokens = references.split()
            smoothie = SmoothingFunction().method4
            score = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothie)
        except Exception:
            score = 0.0
        logger.info(f"bleu_score_metric score: {score}")
        logger.info("Completed bleu_score_metric evaluation strategy")
        return score
    
    def meteor_metric(self, prompts, test_case_responses):
        """
        Compute METEOR score for each predicted sentence vs. its reference.
        Parameters:
        - prompts (list of str): List of reference sentences.
        - test_case_responses (list of str): List of generated/predicted sentences.
        Prints:
        - Average METEOR Score (%)
        """
        logger.info("Starting meteor_metric evaluation strategy")
        try:
            prediction = test_case_responses
            reference = prompts
            if not prediction or not reference:
                score = 0.0
            else:
                prediction_tokens = prediction.split()
                reference_tokens = reference.split()
                score = meteor_score([reference_tokens], prediction_tokens)
        except Exception:
            score = 0.0
        logger.info(f"meteor_metric score: {score}")
        logger.info("Completed meteor_metric evaluation strategy")
        return score


    def rouge_score_metric(self, test_case_responses, expected_responses):
        """
        Com
        pute average ROUGE scores over a batch of predictions and references.
        Parameters:
        - prompts (list of str): Reference (ground truth) sentences.
        - test_case_responses (list of str): Predicted/generated responses.
        Prints:
        - Average ROUGE scores for rouge1, rouge2, rougeL, and rougeLsum.
        """
        logger.info("Starting rouge_score_metric evaluation strategy")
        try:
            rouge = evaluate.load("rouge")
            # all_scores = {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0, 'rougeLsum': 0.0}
            prediction = test_case_responses
            reference = expected_responses
            results = rouge.compute(predictions=[prediction], references=[reference])
            logger.info(f"rouge_score_metric scores: {results}")
            return results
        except Exception as e:
            logger.error(f"rouge_score_metric failed: {str(e)}")
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0, "rougeLsum": 0.0}
    
    def cosine_similarity_metric(self, agent_response:str, expected_response:str) -> float:
        """
        Computes the cosine similarity between 2 sentences using sentence transformers embeddings.
        """
        embedding_model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v1')
        embeddings = embedding_model.encode([agent_response,expected_response])
        similarity = cos_sim(embeddings[0],embeddings[1])
        return similarity[0][0]


    def evaluate(self, agent_response: str, expected_response: Optional[str] = None) -> float:
        """
        Evaluate the agent's response using similarity matching.
        
        :param agent_response: The response generated by the agent.
        :param expected_response: The expected response to compare against.
        :return: A score representing the similarity of the agent's response to the expected response.
        """

        match self.__metric_name:
            case "bert_similarity":
                bertscore = load("bertscore")
                results = bertscore.compute(predictions=[agent_response], references=[expected_response], lang="en")
                return results['f1'][0]  # Return the F1 score from BERTScore
            case "cosine_similarity":
                cos_sim_score = self.cosine_similarity_metric(agent_response,expected_response)
                return cos_sim_score
            case "rouge_similarity":
                score = self.rouge_score_metric(expected_response, agent_response)
                return score
            case "meteor_similarity":
                score = self.meteor_metric(expected_response, agent_response)
                return score
            case "bleu_similarity":
                score = self.bleu_score_metric(expected_response, agent_response)
                return score
            case "bart_score_similarity":
                # Placeholder for BART score similarity logic
                bart_scorer = BARTScorer(device='cpu', checkpoint='facebook/bart-large-cnn')
                score = bart_scorer.score([expected_response], [agent_response], batch_size=4)
                return score[0]
            case _:
                raise ValueError(f"Unknown metric name: {self.__metric_name}")

        return 0.0  # Replace with actual evaluation logic
    
#Test
# sm_instance = SimilarityMatchStrategy(metric_name="bart_score_similarity")
# score = sm_instance.evaluate("hello world","gomenasai")
# print(f"Score: {score}")
# score = sm_instance.evaluate("hello world","hello gokul")
# print(f"Score: {score}")
# score = sm_instance.evaluate("hello world","hello world")
# print(f"Score: {score}")
# del sm_instance
## Similarity Score have been tested and works well.