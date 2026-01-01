from typing import Optional, Dict, List, Tuple
import re
import os
import asyncio
import warnings
from transformers.pipelines import pipeline
from transformers import AutoTokenizer
from .utils import detect_text, google_lang_translate
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("hallucination")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="hallucination")

class HallucinationStrategy(Strategy):
    """
    Strategy for evaluating hallucination metrics across QA, summarization, and MC tasks.
    """
    def __init__(self, name: str = "hallucination", **kwargs) -> None:
        """
        Initializes the HallucinationStrategy with task type and prompt.

        Parameters:
        - name (str): Strategy name.
        - kwargs: Must include 'prompt' (text given to model) and 'source_type' (task type).
        """
        super().__init__(name, kwargs=kwargs)
        self.source_type = name.split("_")[-1] if len(name.split("_")) > 1 else dflt_vals.default_type
        
        self.classifier = pipeline(
            "text-classification",
            model=dflt_vals.model_name,
            tokenizer=AutoTokenizer.from_pretrained(dflt_vals.tokenizer),
            trust_remote_code=True
        )

    def _translate_if_needed(self, text: str) -> str:
        """
        Translates non-English input text to English if needed.

        Parameters:
        - text (str): Input text.

        Returns:
        - str: Translated text in English.
        """
        lang = asyncio.run(detect_text(text))
        if lang == "en":
            return text
        else:
            translated_text = asyncio.run(google_lang_translate(text))
            return translated_text

    def _score_with_vectara_model(self, prompt: str, agent_response: str) -> float:
        """
        Computes hallucination score using Vectara model.

        Parameters:
        - prompt (str): The original input or context.
        - agent_response (str): Model's response to evaluate.

        Returns:
        - float: Score (confidence of being consistent / not hallucinated).
        """
        try:
            input_text = (
                "<pad> Determine if the hypothesis is true given the premise?\n\n"
                f"Premise: {prompt}\nHypothesis: {agent_response}"
            )
            
            results = self.classifier(input_text, top_k=None)
            
            consistent_score = next(
                (score_dict["score"] for score_dict in results 
                 if score_dict["label"].lower() == "consistent"),
                0.0
            )
            
            logger.info(f"Vectara Score (consistent): {consistent_score:.4f}")
            return consistent_score
            
        except Exception as e:
            logger.error(f"Vectara model inference failed: {e}")
            return 0.0

    def halu_qa(self, prompt:str, agent_response: str) -> float:
        """
        Handles QA task hallucination evaluation.

        Parameters:
        - agent_response (str): Response from the agent.

        Returns:
        - float: Hallucination score.
        """
        logger.info("Evaluating Hallucination - QA Task")
        translated_prompt = self._translate_if_needed(prompt)
        translated_resp = self._translate_if_needed(agent_response)
        return self._score_with_vectara_model(translated_prompt, translated_resp)

    def halu_summ(self, prompt:str, agent_response: str) -> float:
        """
        Handles summarization task hallucination evaluation.

        Parameters:
        - agent_response (str): Summarized response.

        Returns:
        - float: Hallucination score.
        """
        logger.info("Evaluating Hallucination - Summarization Task")
        translated_prompt = self._translate_if_needed(prompt)
        translated_resp = self._translate_if_needed(agent_response)
        return self._score_with_vectara_model(translated_prompt, translated_resp)

    def _extract_prediction(self, response: str) -> str:
        """
        Extracts the predicted option (A/B/C/D) from a multiple-choice response.

        Parameters:
        - response (str): Agent's multiple-choice response.

        Returns:
        - str: Predicted choice (A/B/C/D) or "NA" if invalid.
        """
        response = response.strip().lower()
        response_clean = re.sub(r"[^a-zA-Z]", "", response.split()[0].upper())
        if response_clean in ["A", "B", "C", "D"]:
            return response_clean
        return "NA"

    def mc(self, agent_response: str, expected_response: str) -> float:
        """
        Evaluates hallucination in multiple-choice format by checking correctness.

        Parameters:
        - agent_response (str): Model's chosen option.
        - expected_response (str): Correct option (A/B/C/D).

        Returns:
        - float: 1.0 if correct, else 0.0.
        """
        logger.info("Evaluating Hallucination - Multiple Choice Task")
        translated_resp = self._translate_if_needed(agent_response)
        prediction = self._extract_prediction(translated_resp)
        score = 1.0 if prediction == expected_response.upper() else 0.0
        logger.info(f"Agent Response: {agent_response} | Prediction: {prediction} | Expected: {expected_response} | Score: {score}")
        return score

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Main evaluation entrypoint for hallucination across all task types.

        Parameters:
        - agent_response (str): Agent output.
        - expected_response (str, optional): Expected answer (for MC tasks).

        Returns:
        - float: Consistency score (or 1.0/0.0 for MC).
        """
        logger.info(f"Evaluating Hallucination for source type: {self.source_type}")
        if self.source_type == "haluqa":
            return self.halu_qa(testcase.prompt.user_prompt, conversation.agent_response), OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), self.halu_qa(testcase.prompt.user_prompt, conversation.agent_response))
        elif self.source_type == "halusumm":
            return self.halu_summ(testcase.prompt.user_prompt, conversation.agent_response), OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), self.halu_summ(testcase.prompt.user_prompt, conversation.agent_response))
        elif self.source_type == "mc":
            if testcase.response.response_text is None:
                logger.warning("Expected response required for MC task")
                return 0.0, OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), 0.0)
            return self.mc(conversation.agent_response, testcase.response.response_text), OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), self.mc(conversation.agent_response, testcase.response.response_text))
        else:
            logger.warning(f"Unsupported source type: {self.source_type}")
            return 0.0, ""