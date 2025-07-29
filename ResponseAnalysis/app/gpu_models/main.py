# @author Sudarsun S
# @date 2025-07-24
# @description This module initializes the Sarvam AI translator instance for use in the application.

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import argparse, logging
import sys, os
from typing import Optional

from translator import SarvamAITranslator
from generator import SarvamAIGenerator
from safety import ShieldGemmaSafety

# Adjust the path to include the "lib" directory
sys.path.append(os.path.dirname(__file__) + "/../../")  

# from lib.utils.logger import get_logger
from logger import get_logger

# # Request/Response Models
# class SafetyEvalRequest(BaseModel):
#     prompt: str
#     agent_response: str
#     metric: str  # misuse | jailbreak | exaggerated_safety

# class SafetyEvalResponse(BaseModel):
#     score: float
#     label: str

app = FastAPI(title="Sarvam AI Application")
translator = SarvamAITranslator()
generator = SarvamAIGenerator()

safety_engine: Optional[ShieldGemmaSafety] = None

@app.post("/translate")
def translate_text(input_text: str, target_language: str):
    """
    Translate the input text to the target language using Sarvam AI.
    """
    if translator.api_key_check:
        logger.info("The Sarvam Model will get loaded to your machine!")
        translated_text = translator.translate(input_text, target_language)
    else:
        logger.info("The Sarvam API Key is used!")
        translated_text = translator.token_translate(input_text, target_language)
    return {"input": input_text, "translated": translated_text, "language": target_language}

@app.post("/generate")
def generate_text(prompt: str, max_new_tokens: int = 1024):
    """
    Generate text continuation from a given prompt using Sarvam AI.
    """
    generated_text = generator.generate(prompt, max_new_tokens)
    return {"prompt": prompt, "generated": generated_text}

@app.post("/embedding")
def get_embedding(text: str):
    """
    Get the embedding for the input text using Sarvam AI.
    """
    embedding = generator.get_embedding(text)
    embedding = embedding.tolist()  # Convert numpy array to list for JSON serialization
    print("Final embedding length:", len(embedding))
    return {"text": text, "embedding": embedding}

@app.post("/safety_eval")
def evaluate_safety(prompt: str, agent_response: str, metric_name: str):
    """
    Get the Safety Violation score using Google Shieldgemma-2b model
    """
    try:
        score = safety_engine.evaluate(prompt=prompt, response=agent_response, metric=metric_name)
        label = "Violation Likely" if score >= 0.5 else "No Violation"
        return {"score": score, "label": label}
    except Exception as e:
        raise Exception(f"Safety evaluation failed: {str(e)}")

if __name__ == "__main__":
    # Parse command line arguments for host and port
    parser = argparse.ArgumentParser(description="Sarvam AI application")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to run the FastAPI application", dest="port")
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="Host to run the FastAPI application", dest="host")
    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int, default=5, help="Verbosity level for logging", choices=[0,1,2,3,4,5])
    parser.add_argument("--translator-model", "-t", type=str, default="sarvamai/sarvam-translate", help="Sarvam AI translation model name", dest="translator_model")
    parser.add_argument("--generator-model", "-g", type=str, default="sarvamai/sarvam-2b-v0.5", help="Sarvam AI generator model name", dest="generator_model")
    parser.add_argument("--safety-model", "-s", type=str, default="google/shieldgemma-2b", help="ShieldGemma safety model name", dest="safety_model")
    parser.add_argument("--force-cpu", action="store_true", help="Force CPU usage for the translator model", dest="force_cpu")

    args = parser.parse_args()

    # Set up logging
    logger = get_logger(__name__)

    verbosity_levels = {
        5: logging.DEBUG,  # Verbose output
        4: logging.INFO,   # Default output
        3: logging.WARNING,  # Warning output
        2: logging.ERROR,    # Error output
        1: logging.CRITICAL,  # Critical output
        0: logging.NOTSET,    # No output
    }

    # Set the logging level based on the verbosity argument
    if args.verbosity in verbosity_levels:
        loglevel = verbosity_levels[args.verbosity]
        logger.setLevel(loglevel)
    else:
        logger.error(f"Invalid verbosity level: {args.verbosity}. Valid levels are: {list(verbosity_levels.keys())}")
        exit(0)

    logger.debug(f"Starting Sarvam AI and Shieldgemma application")

    # Initialize the translator and generator with the specified log level
    translator = SarvamAITranslator(loglevel=loglevel, force_cpu=True)
    translator.load_model(model_name=args.translator_model)

    generator = SarvamAIGenerator(loglevel=loglevel, force_cpu=args.force_cpu)
    generator.load_model(model_id=args.generator_model)

    safety_engine = ShieldGemmaSafety(metric="misuse", loglevel=loglevel)
    safety_engine.load_model()

    # Run the FastAPI application
    uvicorn.run(app, host=args.host, port=args.port)