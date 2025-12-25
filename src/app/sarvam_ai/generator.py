# @author: Sudarsun S
# @date: 2025-07-24
# @description: This module initializes the Sarvam AI application with text generation capabilities.

# Sarvam AI text generation model wrapper
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel
import torch
import sys, os, logging
import numpy as np
from sarvamai import SarvamAI
import math
from pydantic import BaseModel
from typing import Optional, List

# Adjust the path to include the "lib" directory
sys.path.append(os.path.dirname(__file__) + "/../../")  
from dotenv import load_dotenv
load_dotenv()

from lib.utils.logger import get_logger
# from logger import get_logger

class Request(BaseModel):
    text : str
    layers : Optional[List[int]] = None
    sent_vec : Optional[bool] = None
    pool : Optional[str] = "mean"

class SarvamAIGenerator:
    """ Sarvam AI text generation model wrapper.
    This class provides methods to generate text and obtain embeddings using the Sarvam AI model.
    """
    def __init__(self, loglevel=logging.DEBUG, force_cpu=False):
        self.force_cpu = force_cpu
        self.logger = get_logger(__name__, loglevel=loglevel)
        self.model_loaded = False
        self.api_key_check = bool(os.environ.get('SARVAM_API_KEY'))
        self.device = torch.device("cuda")

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

    def token_completion(self, text:str):
        """
        This function is for chat completion using Sarvam APIs
        """  
        SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
        client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
        response = client.chat.completions(
            messages= [
                {
                    "role":"user",
                    "content":text
                }
            ]
        )
        return response.choices[0].message.content
    
    def get_perplexity(self, text:str):
        """
        This function basically returns the perplexity obtained from a text.
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            perplexity = math.exp(loss.item()) # this calculates the perplexity in the text -> e ^(- 1/N SUM(1->N) (log(w_{i}|c_{0:i-1})) )
        return perplexity

    def get_SLOR(self, text:str):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        seq_len = inputs["input_ids"].size(1)
        with torch.no_grad():
            outputs = self.model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            log_prob = -1 * loss.item() * seq_len
        vocab_size = len(self.tokenizer.get_vocab())
        unigram_prob = 1.0 / vocab_size
        uni_log_prob = seq_len * math.log(unigram_prob)

        return (log_prob - uni_log_prob) / seq_len
    
    def early_embedding(self, text):
        try:
            model_name = "ai4bharat/IndicBERTv2-MLM-only"
            tokenizer_ = AutoTokenizer.from_pretrained(model_name)
            model_ = AutoModel.from_pretrained(model_name, output_hidden_states=True).to(self.device)
        except:
            self.logger.error("Could not load embedding model due to insufficient memory.")
        model_.eval()
        enc = tokenizer_(text, return_tensors="pt", truncation=True).to(self.device)
        with torch.no_grad():
            outputs = model_(**enc, output_hidden_states=True, return_dict=True)

        layer_id = 2 # early layer that supposedly captures morphological information
        h = outputs.hidden_states[layer_id][0]  # [seq_len, hidden_dim]
        h = h - h.mean(dim=0, keepdim=True)
        h = h / (h.norm(dim=-1, keepdim=True) + 1e-12)
        vec = h.mean(dim=0)
        vec = vec / (vec.norm() + 1e-12)
        return vec.cpu().tolist()


