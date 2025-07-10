from strategy_base import Strategy
from typing import Optional
from opik.evaluation.metrics import GEval
import logging
import warnings
from langchain_community.llms import Ollama
import re
from logger import get_logger
from tqdm import tqdm
import os
from utils import load_json,save_json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer


logger = get_logger("robustness")

warnings.filterwarnings("ignore")

# This module implements "Robustness Out of Domain" strategy to analyze the agent response.
class Robustness_OutOfDomain(Strategy):
    def __init__(self, name: str = "robustness_ood", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__model_name = kwargs.get("model_name","LibrAI/longformer-harmful-ro")
        self.__device = kwargs.get("device","cpu")
        self.__save_dir = kwargs.get("save_dir","saved_evaluations")
        self.model = AutoModelForSequenceClassification.from_pretrained(self.__model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.__model_name)
        self.classifier = pipeline('text-classification', model=self.model, tokenizer=self.tokenizer, device=self.__device)
        if not os.path.exists(self.__save_dir):
            os.makedirs(self.__save_dir)

    def model_evaluate(self, data, resume=False, progress_filename='longformer_eval.json'):
        """
        Evaluate a dataset using the loaded Hugging Face model.

        Args:
            data: List of data to be evaluated.
            resume (bool): Whether to resume from a saved progress file. Default is False.
            progress_filename (str): Filename for saving or resuming progress.

        Returns:
            List: The evaluated data.
        """
        if resume:
            load_path = os.path.join(self.__save_dir, progress_filename)
            try:
                data = load_json(load_path)
                logging.info("Resuming evaluation from saved progress.")
            except FileNotFoundError:
                logging.warning("No saved progress file found at %s. Starting a new evaluation.", load_path)

        assert isinstance(data, list), "Data must be a list."
        logging.info('Total data number: {}'.format(len(data)))
        # Filter out invalid data
        data = [el for el in data if el['res'] is not None and el != ""]
        logging.info('Total data number: %d', len(data))
        logging.info('Evaluating...')

        evaluated_data = self._evaluate_batch(data)

        save_json(data, os.path.join(self.__save_dir, progress_filename))
        return evaluated_data
    
    def _evaluate_batch(self,data, batch_size=32, progress_filename='longformer_eval.json'):
        results = []
        for i in tqdm(range(0, len(data), batch_size)):
            batch = data[i:i+batch_size]
            texts = [item.get('res', '') for item in batch if 'eval_res' not in item]
            if texts:
                try:
                    batch_outputs = self.classifier(texts)
                    assert len(batch_outputs) == len(texts)
                    idx = 0
                    for item in batch:
                        if 'eval_res' not in item:
                            item['eval_res'] = batch_outputs[idx]["label"]
                            idx += 1
                    results.extend(batch)
                    logging.info("Processed batch from %s to %s", i, i+batch_size)
                except Exception as e:
                    logging.error("Error processing batch %s to %s: %s", i, i+batch_size, str(e))
                    save_json(data, os.path.join(self.__save_dir, progress_filename))
                    raise
            else:
                results.extend(batch)
        return results

    def ood_detection(self, agent_prompt, agent_response):
        eval_res = self.model_evaluate([{"prompt":agent_prompt,"res":agent_response}])
        return eval_res[0]


    def evaluate(self, agent_response: str, agent_prompt:str, expected_response: Optional[str] = None):
        """
        Evaluate the agents response for Robustness Adv Instruction using Cosine Similarity.
        """
        return self.ood_detection(agent_prompt=agent_prompt,agent_response=agent_response)
    
# #Test
# rbadv_instance = Robustness_OutOfDomain(device="cpu")
# score = rbadv_instance.evaluate(agent_prompt="Can you check if there are any trending discussions related to the Sakura festival occurring in Japan on Google Trends or Twitter?\n",agent_response="Yes it is possible, and it does have a method that implements this, but you don't want to use it directly. To demonstrate how and how not to use it, let's create an empty dict with the dict literal,\n")
# print(f"Answer: {score}")
# del rbadv_instance
# ## Robustness_AdvInstruction is working!