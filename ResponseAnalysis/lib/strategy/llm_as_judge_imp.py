import requests
import json
from typing import List, Dict, Any, Optional
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM


class OllamaModel(DeepEvalBaseLLM):
    """Custom Ollama model wrapper for DeepEval"""
    
    def __init__(self, model_name: str, base_url: str = "http://10.21.186.219:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
    
    def load_model(self):
        """Load model - not needed for Ollama as it's already running"""
        pass
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Ollama model"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Ollama API: {str(e)}")
    
    async def a_generate(self, prompt: str, **kwargs) -> str:
        """Async generate - using sync for simplicity"""
        return self.generate(prompt, **kwargs)
    
    def get_model_name(self) -> str:
        return self.model_name


def create_geval_metric(
    name: str,
    criteria: str,
    evaluation_params: List[str],
    model: OllamaModel,
    threshold: float = 0.5
) -> GEval:
    """Create a G-Eval metric with custom Ollama model"""
    return GEval(
        name=name,
        criteria=criteria,
        evaluation_params=evaluation_params,
        evaluation_steps=[
            "Read the input and expected output carefully",
            "Evaluate the actual output against the criteria",
            "Assign a score from 0 to 1 based on how well the criteria is met",
            "Provide reasoning for the score"
        ],
        model=model,
        threshold=threshold
    )


def run_geval_with_ollama(
    model_name: str,
    test_cases: List[Dict[str, str]],
    base_url: str = "http://10.21.186.219:11434",
    custom_criteria: Optional[str] = None
):
    """
    Run G-Eval using Ollama model
    
    Args:
        model_name: Name of the model in Ollama (e.g., 'llama2', 'mistral')
        test_cases: List of test cases with 'input', 'actual_output', 'expected_output'
        base_url: Ollama server URL
        custom_criteria: Custom evaluation criteria
    """
    
    # Initialize Ollama model
    ollama_model = OllamaModel(model_name=model_name, base_url=base_url)
    
    # Default criteria if none provided
    if custom_criteria is None:
        custom_criteria = """
        Evaluate the quality of the response based on:
        1. Accuracy and correctness of information
        2. Relevance to the input question
        3. Clarity and coherence of explanation
        4. Completeness of the answer
        """
    
    # Create G-Eval metric
    geval_metric = create_geval_metric(
        name="Custom Quality Evaluation",
        criteria=custom_criteria,
        evaluation_params=["input", "actual_output"],
        model=ollama_model,
        threshold=0.7
    )
    
    # Convert test cases to LLMTestCase objects
    llm_test_cases = []
    for case in test_cases:
        test_case = LLMTestCase(
            input=case["input"],
            actual_output=case["actual_output"],
            expected_output=case.get("expected_output", "")
        )
        llm_test_cases.append(test_case)
    
    # Run evaluation
    results = evaluate(
        test_cases=llm_test_cases,
        metrics=[geval_metric]
    )
    
    return results


# Example usage
if __name__ == "__main__":
    # Example test cases
    sample_test_cases = [
        {
            "input": "What is the capital of France?",
            "actual_output": "The capital of France is Paris, which is located in the north-central part of the country.",
            "expected_output": "Paris"
        },
        {
            "input": "Explain photosynthesis in simple terms",
            "actual_output": "Photosynthesis is the process where plants use sunlight, water, and carbon dioxide to make their own food and release oxygen.",
            "expected_output": "Plants convert sunlight, water and CO2 into glucose and oxygen"
        },
        {
            "input": "What is 2 + 2?",
            "actual_output": "2 plus 2 equals 4",
            "expected_output": "4"
        }
    ]
    
    # Custom evaluation criteria
    custom_criteria = """
    Evaluate the response quality based on:
    1. Factual accuracy (40%)
    2. Completeness of answer (30%)
    3. Clarity and readability (20%)
    4. Relevance to question (10%)
    
    Score from 0 to 1 where:
    - 0.9-1.0: Excellent response
    - 0.7-0.8: Good response
    - 0.5-0.6: Average response
    - 0.3-0.4: Poor response
    - 0.0-0.2: Very poor response
    """
    
    try:
        # Run evaluation with your Ollama model
        results = run_geval_with_ollama(
            model_name="llama3.1:latest",  # Replace with your model name
            test_cases=sample_test_cases,
            base_url="http://10.21.186.219:11434",  # Update if different
            custom_criteria=custom_criteria
        )
        
        print("Evaluation Results:")
        print("=" * 50)
        
        for i, result in enumerate(results):
            print(f"\nTest Case {i + 1}:")
            print(f"Input: {sample_test_cases[i]['input']}")
            print(f"Actual Output: {sample_test_cases[i]['actual_output']}")
            print(f"Score: {result.metrics[0].score}")
            print(f"Reason: {result.metrics[0].reason}")
            print(f"Success: {result.metrics[0].is_successful()}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error running evaluation: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Verify your model is available: ollama list")
        print("3. Check if the model name is correct")
        print("4. Ensure the Ollama server URL is accessible")


# Additional utility functions

def check_ollama_connection(base_url: str = "http://10.21.186.219:11434") -> bool:
    """Check if Ollama server is accessible"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        return response.status_code == 200
    except:
        return False


def list_ollama_models(base_url: str = "http://10.21.186.219:11434") -> List[str]:
    """List available models in Ollama"""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    except:
        return []


def test_ollama_model(model_name: str, base_url: str = "http://10.21.186.219:11434") -> bool:
    """Test if a specific model works in Ollama"""
    try:
        ollama_model = OllamaModel(model_name, base_url)
        response = ollama_model.generate("Hello, how are you?")
        return len(response.strip()) > 0
    except:
        return False


# Setup verification
def verify_setup():
    """Verify that everything is set up correctly"""
    print("Verifying Ollama setup...")
    
    if not check_ollama_connection():
        print("❌ Cannot connect to Ollama server")
        print("   Make sure Ollama is running: ollama serve")
        return False
    
    print("✅ Ollama server is accessible")
    
    models = list_ollama_models()
    if not models:
        print("❌ No models found in Ollama")
        print("   Install a model: ollama pull llama2")
        return False
    
    print(f"✅ Found {len(models)} models: {', '.join(models)}")
    
    # Test first model
    test_model = models[0]
    if test_ollama_model(test_model):
        print(f"✅ Model '{test_model}' is working")
        return True
    else:
        print(f"❌ Model '{test_model}' is not responding")
        return False


if __name__ == "__main__":
    #Uncomment to verify setup first
    if verify_setup():
        print("\n" + "="*50)
        print("Setup verified! You can now run the evaluation.")
    else:
        print("\nPlease fix the issues above before running evaluation.")