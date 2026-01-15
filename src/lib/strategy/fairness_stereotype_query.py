from typing import Optional
from tqdm import tqdm
import os
from transformers.pipelines import pipeline
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging
import warnings
from lib.data import TestCase, Conversation
from .strategy_base import Strategy
from .logger import get_logger
from .utils_new import FileLoader, OllamaConnect
from .utils import load_json, save_json, RtA

warnings.filterwarnings("ignore")

FileLoader._load_env_vars(__file__)
logger = get_logger("fairness_stereotype_query")
dflt_vals = FileLoader._to_dot_dict(__file__, os.getenv("DEFAULT_VALUES_PATH"), simple=True, strat_name="fairness_stereotype_query")

class Fairness_Stereotype_Query(Strategy):
    def __init__(self, name: str = "fairness_stereotype_query", **kwargs) -> None:
        super().__init__(name, kwargs=kwargs)
        self.__model_name = dflt_vals.model_name
        self.__device = dflt_vals.device
        self.__save_dir = dflt_vals.save_dir
        self.model = AutoModelForSequenceClassification.from_pretrained(self.__model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.__model_name)
        self.classifier = pipeline('text-classification', model=self.model, tokenizer=self.tokenizer, device=self.__device)
        if not os.path.exists(self.__save_dir):
            os.makedirs(self.__save_dir)

    def model_evaluate(self, data, resume=False, progress_filename='longformer_eval.json'):
        """
        Evaluate a dataset using the loaded Hugging Face model.

        :param  data: List of data to be evaluated.
        :param resume (bool): Whether to resume from a saved progress file. Default is False.
        :param progress_filename (str): Filename for saving or resuming progress.

        returns: List: The evaluated data.
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
    
    def stereotype_query_detection(self, agent_response: str):
        """
        Detects stereotypes in the agent's response.
        """
        eval_res = self.model_evaluate([{"res":agent_response}])
        return RtA(eval_res)

    def evaluate(self, testcase:TestCase, conversation:Conversation):
        """
        Evaluate the agents response for Fairness Stereotype Query.
        """
        score = self.stereotype_query_detection(conversation.agent_response)
        logger.info(f"Fairness Stereotype Query Score: {score}")
        reason = OllamaConnect.get_reason(conversation.agent_response, " ".join(self.name.split("_")), score)
        return score, reason