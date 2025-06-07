import json
import pandas as pd
from googletrans import Translator
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import language_tool_python
from dotenv import load_dotenv
import time
import asyncio

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from opik.integrations.langchain import OpikTracer
from opik.evaluation.metrics import GEval
from opik import Opik
import litellm
from lexical_diversity import lex_div as ld
from tqdm import tqdm
import evaluate
from nltk.translate.meteor_score import meteor_score
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import warnings
import logging
from datetime import datetime
import logging

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
load_dotenv()
litellm.drop_params = True
model_name = "llama3.2:1b"
llm = OllamaLLM(model=model_name)

with open('Data/DataPoints.json', 'r', encoding='utf-8') as f:
    datapoints = json.load(f)

with open('Data/plans.json', 'r', encoding='utf-8') as f:
    plans = json.load(f)

with open('Data/responses.json', 'r', encoding='utf-8') as f:
    responses = json.load(f)

with open('Data/strategy_map.json', 'r', encoding='utf-8') as f:
    strategy_map = json.load(f)

embedding_model = SentenceTransformer("thenlper/gte-small")


async def language_coverage(prompts, test_case_responses):
    """
    Strategy 1
    Calculate the language coverage of the response using language detection.
    """
    logger.info("Starting language_coverage evaluation strategy")
    result = []
    async with Translator() as translator:
        for i in range(len(prompts)):
            response_language = await translator.detect(test_case_responses[i])
            prompt_language = await translator.detect(prompts[i])
            score = 1.0 if response_language.lang == prompt_language.lang else 0.0
            result.append(score)
            logger.info(f"language coverage score for batch {i}: {'match' if score else 'mismatch'}")
    logger.info("Completed language_coverage evaluation strategy")
    return result


async def language_coverage_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 2
    Calculate the language coverage of the response by bringing the langauges to the same plane.
    This is done by translating the response to a single language ie English and then checking if they match.
    """
    logger.info("Starting language_coverage_similarity evaluation strategy")
    result = []
    translator = Translator()
    for i in range(len(prompts)):
        response_language = await translator.translate(test_case_responses[i], dest='en')
        prompt_language = await translator.translate(prompts[i], dest='en')
        expected_response_language = await translator.translate(expected_responses[i], dest='en')
        embeddings = embedding_model.encode([response_language.text, prompt_language.text, expected_response_language.text], show_progress_bar=False)
        similarity = cos_sim(embeddings[0], embeddings[1])
        similarity_2 = cos_sim(embeddings[1], embeddings[2])
        score = 1.0 if similarity > 0.8 or similarity_2 > 0.8 else 0.0
        result.append(score)
        logger.info(f"language_coverage_similarity score for batch {i}: {score}")
    logger.info("Completed language_coverage_similarity evaluation strategy")
    return result


def llm_as_judge(metric_name, task_intro, judge_prompt, system_prompt, prompts, test_case_response, expected_response):
    """
    Strategy 3
    Use an LLM to judge the language coverage of the response.
    """
    logger.info(f"Starting llm_as_judge evaluation strategy for {metric_name}")
    result = []
    metric = GEval(
        name=metric_name,
        task_introduction=task_intro,
        evaluation_criteria=judge_prompt,
        model=f'ollama_chat/{model_name}'
    )
    for i in range(len(prompts)):
        score = metric.score(
            input=prompts[i],
            output=test_case_response[i],
            expected_output=expected_response[i],
            context=system_prompt
        )
        result.append(score.value)
        logger.info(f"llm_as_judge score for batch {i}: {score.value}")
    logger.info("Completed llm_as_judge evaluation strategy")
    return result


def text_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 4
    Use text similarity to check if the response matches the prompt.
    """
    logger.info("Starting text_similarity evaluation strategy")
    result = []
    for i in range(len(prompts)):
        embeddings = embedding_model.encode([prompts[i], test_case_responses[i], expected_responses[i]])
        similarity = cos_sim(embeddings[0], embeddings[1])
        similarity_2 = cos_sim(embeddings[1], embeddings[2])
        score = 1.0 if similarity > 0.8 or similarity_2 > 0.8 else 0.0
        result.append(score)
        logger.info(f"text_similarity score for batch {i}: {score}")
    logger.info("Completed text_similarity evaluation strategy")
    return result


def toxicity_model_result(test_case_responses):
    """
    Strategy 5
    Use a toxicity model to check if the response matches the prompt.
    """
    logger.info("Starting toxicity_model_result evaluation strategy")
    tokenizer = AutoTokenizer.from_pretrained("nicholasKluge/ToxicityModel")
    all_tokens = []
    for response in test_case_responses:
        tokens = tokenizer(response, truncation=True, max_length=512, return_token_type_ids=False, return_tensors="pt", return_attention_mask=True)
        all_tokens.append(tokens)
    model = AutoModelForSequenceClassification.from_pretrained("nicholasKluge/ToxicityModel")
    model.eval()
    model.to("cpu")
    result = []
    for i, token in enumerate(all_tokens):
        score = model(**token)[0].item()
        val = -1.0 if score < 0 else 1.0
        result.append(val)
        logger.info(f"toxicity_model_result score for batch {i}: {val}")
    logger.info("Completed toxicity_model_result evaluation strategy")
    return result


def grammarChecker(text):
    tool = language_tool_python.LanguageTool('en-US')
    result = tool.check(text)
    return result


async def grammarcheck(test_case_responses):
    """
    Strategy 6
    Checks the grammatical correctness
    """
    logger.info("Starting grammarcheck evaluation strategy")
    translator = Translator()
    result = []
    for i, response in enumerate(test_case_responses):
        response_language = await translator.detect(response)
        response_translation = await translator.translate(response, dest='en') if response_language.lang != "en" else response
        response_translation = response_translation.text if hasattr(response_translation, 'text') else response_translation
        grammar_check = grammarChecker(response_translation)
        score = 0.0 if len(grammar_check) > 1 else 1.0
        result.append(score)
        logger.info(f"grammarcheck score for batch {i}: {score}")
    logger.info("Completed grammarcheck evaluation strategy")
    return result


async def lexical_diversity(test_case_responses):
    """
    Strategy 7
    Checks the lexical diversity
    """
    logger.info("Starting lexical_diversity evaluation strategy")
    ld_cal = []
    translator = Translator()
    for i, response in enumerate(test_case_responses):
        response_language = await translator.detect(response)
        response_translation = await translator.translate(response, dest='en') if response_language.lang != "en" else response
        response_translation = response_translation.text if hasattr(response_translation, 'text') else response_translation
        flt = ld.flemmatize(response_translation)
        score = ld.mattr(flt)
        ld_cal.append(score)
        logger.info(f"lexical_diversity score for batch {i}: {score}")
    logger.info("Completed lexical_diversity evaluation strategy")
    return ld_cal


def bleu_score_metric(predictions, references):
    """
    Strategy 8 : Calculates the BLEU score between predicted and reference texts.

    Parameters:
    - predictions (list of str): List of predicted output sentences.
    - references (list of str): List of reference (ground truth) sentences.

    Prints:
    - Average BLEU Score (%)
    """
    logger.info("Starting bleu_score_metric evaluation strategy")
    result = []
    for i in range(len(predictions)):
        try:
            pred_tokens = predictions[i].split()
            ref_tokens = references[i].split()
            smoothie = SmoothingFunction().method4
            score = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothie)
            result.append(score)
        except Exception:
            score = 0.0
            result.append(score)
        logger.info(f"bleu_score_metric score for batch {i}: {score}")
    logger.info("Completed bleu_score_metric evaluation strategy")
    return result


def meteor_metric(prompts, test_case_responses):
    """
    Strategy 9 : Compute METEOR score for each predicted sentence vs. its reference.
    Parameters:
    - prompts (list of str): List of reference sentences.
    - test_case_responses (list of str): List of generated/predicted sentences.
    Prints:
    - Average METEOR Score (%)
    """
    logger.info("Starting meteor_metric evaluation strategy")
    results = []
    for i in range(len(prompts)):
        try:
            prediction = test_case_responses[i]
            reference = prompts[i]
            if not prediction or not reference:
                score = 0.0
            else:
                prediction_tokens = prediction.split()
                reference_tokens = reference.split()
                score = meteor_score([reference_tokens], prediction_tokens)
        except Exception:
            score = 0.0
        results.append(score)
        logger.info(f"meteor_metric score for batch {i}: {score}")
    logger.info("Completed meteor_metric evaluation strategy")
    return results


def rouge_score_metric(prompts, test_case_responses):
    """
    Strategy 10 : Compute average ROUGE scores over a batch of predictions and references.
    Parameters:
    - prompts (list of str): Reference (ground truth) sentences.
    - test_case_responses (list of str): Predicted/generated responses.
    Prints:
    - Average ROUGE scores for rouge1, rouge2, rougeL, and rougeLsum.
    """
    logger.info("Starting rouge_score_metric evaluation strategy")
    try:
        rouge = evaluate.load("rouge")
        all_scores = {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0, 'rougeLsum': 0.0}
        total = len(prompts)
        for i in range(total):
            prediction = test_case_responses[i]
            reference = prompts[i]
            results = rouge.compute(predictions=[prediction], references=[reference])
            for key in all_scores:
                all_scores[key] += float(results.get(key, 0.0))
        avg_scores = {k: (v / total) for k, v in all_scores.items()}
        logger.info(f"rouge_score_metric average scores: {avg_scores}")
        return avg_scores
    except Exception as e:
        logger.error(f"rouge_score_metric failed: {str(e)}")
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0, "rougeLsum": 0.0}
