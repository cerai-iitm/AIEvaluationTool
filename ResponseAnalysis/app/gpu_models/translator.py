# @author Sudarsun S
# @date 2025-07-24
# @description This module provides a function to translate text using the Sarvam AI translation service.

from transformers import AutoModelForCausalLM, AutoTokenizer
import sys, os
import logging
import torch

# Adjust the path to include the "lib" directory
sys.path.append(os.path.dirname(__file__) + "/../../")  

# from lib.utils.logger import get_logger
from logger import get_logger

class SarvamAITranslator:
    def __init__(self, loglevel=logging.DEBUG, force_cpu=False):
        self.model_loaded = False
        self.logger = get_logger(__name__, loglevel=loglevel)
        self.force_cpu = force_cpu

    def load_model(self, model_name="sarvamai/sarvam-translate"):
        self.model_name = model_name
        self.logger.debug(f"Loading Sarvam AI translation model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if torch.cuda.is_available() and not self.force_cpu:
            current_device = torch.cuda.current_device()
            print(f"Current CUDA device ID: {current_device}")
            self.logger.info("using GPU for inferring from Sarvam translation model")
            self.device = torch.device("cuda")
        else:
            self.logger.info("using CPU for inferring from Sarvam translation model")
            self.device = torch.device("cpu")

        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model_loaded = True

    def translate(self, input_text, target_language):
        # Load the model if not already loaded
        if not self.model_loaded:
            self.load_model()

        template = [{"role": "system", "content": f"Translate the text below to {target_language}."},
                    {"role": "user", "content": input_text}]

        # Apply chat template to structure the conversation
        text = self.tokenizer.apply_chat_template(template, tokenize=False,
                                                  add_generation_prompt=True)

        # Tokenize and move input to model device
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        # Generate the output
        generated_ids = self.model.generate(**model_inputs, max_new_tokens=1024,
                                            do_sample=False, temperature=0.01,
                                            num_return_sequences=1)
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
        output_text = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        return output_text.strip()