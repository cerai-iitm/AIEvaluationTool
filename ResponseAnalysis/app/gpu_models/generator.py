# @author: Sudarsun S
# @date: 2025-07-24
# @description: This module initializes the Sarvam AI application with text generation capabilities.

# Sarvam AI text generation model wrapper
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import sys, os, logging
import numpy as np

# Adjust the path to include the "lib" directory
sys.path.append(os.path.dirname(__file__) + "/../../")  

# from lib.utils.logger import get_logger
from logger import get_logger

class SarvamAIGenerator:
    """ Sarvam AI text generation model wrapper.
    This class provides methods to generate text and obtain embeddings using the Sarvam AI model.
    """
    def __init__(self, loglevel=logging.DEBUG, force_cpu=False):
        self.force_cpu = force_cpu
        self.logger = get_logger(__name__, loglevel=loglevel)
        self.model_loaded = False

    def load_model(self, model_id: str = "sarvamai/sarvam-2b-v0.5"):
        """ Load the Sarvam AI model for text generation.
        This method checks if the model is already loaded and loads it if not.
        It uses GPU if available, otherwise falls back to CPU.
        """
        self.logger.debug(f"Loading Sarvam AI generator model: {model_id}")
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

        if torch.cuda.is_available() and not self.force_cpu:
            self.logger.info("using GPU for infering from Sarvam generator model")
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, 
                                                              torch_dtype=torch.float16, device_map="cuda")
            current_device = torch.cuda.current_device()
            print(f"Current CUDA device ID: {current_device}")
            self.device = torch.device("cuda")
        else:
            self.logger.info("using CPU for infering from Sarvam generator model")
            self.model = AutoModelForCausalLM.from_pretrained(self.model_id, 
                                                              torch_dtype=torch.float32)
            self.device = torch.device("cpu")
        # Move model to the appropriate device
        self.model.to(self.device)
        self.model_loaded = True

    def generate(self, prompt: str, max_new_tokens: int = 1024) -> str:
        """
        Generate text continuation from a given prompt.
        """
        if not self.model_loaded:
            self.load_model()

        current_device = torch.cuda.current_device()
        print(f"Current CUDA device ID: {current_device}")

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        inputs = {k: v for k, v in inputs.items() if k in ['input_ids', 'attention_mask']}
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Return mean pooled embedding from last hidden state.
        """
        current_device = torch.cuda.current_device()
        print(f"Current CUDA device ID: {current_device}")
        print(f"Model device: {next(self.model.parameters()).device}")

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        print("Tokenized input keys:", inputs.keys())

        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            print("Model output keys:", outputs.keys() if isinstance(outputs, dict) else dir(outputs))

            last_hidden = outputs.hidden_states[-1] 
            print("Last hidden state shape:", last_hidden.shape)

            embedding = last_hidden.mean(dim=1).squeeze()
            print("Final embedding shape:", embedding.shape)

            # Convert to numpy array for compatibility with other libraries
            return embedding.cpu().numpy()  