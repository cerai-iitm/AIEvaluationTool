 
import requests
from typing import Any
from opik.evaluation.models import OpikBaseModel

class CustomOllamaCompatibleModel(OpikBaseModel):
    def __init__(self, model_name: str, base_url: str):
        super().__init__(model_name)
        self.base_url = base_url  # e.g., "http://10.21.186.219:11434/api/chat"
        self.headers = {
            "Content-Type": "application/json"
        }

    def generate_string(self, input: str) -> str:
        """
        This method is used as part of LLM as a Judge metrics to take a string prompt,
        pass it to the model as a user message and return the model's response as a string.
        """
        conversation = [
            {
                "content": input,
                "role": "user",
            },
        ]
        provider_response = self.generate_provider_response(messages=conversation)

        # Handle Ollama's response format
        if "message" in provider_response and "content" in provider_response["message"]:
            return provider_response["message"]["content"]
        elif "response" in provider_response:
            # Alternative response format
            return provider_response["response"]
        else:
            raise ValueError(f"Unexpected response format: {provider_response}")

    def generate_provider_response(self, messages: list[dict[str, Any]], **kwargs) -> Any:
        """
        This method is used as part of LLM as a Judge metrics to take a list of AI messages,
        pass it to the model and return the full model response.
        """
        # Filter out unsupported parameters for Ollama
        unsupported_params = ['logprobs', 'top_logprobs', 'response_format', 'tools', 'tool_choice']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in unsupported_params}

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            **filtered_kwargs  # Include any other supported parameters
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling model API: {e}")
        except ValueError as e:
            raise Exception(f"Error parsing response: {e}")

# Test the corrected implementation
if __name__ == "__main__":
    # Example usage
    model = CustomOllamaCompatibleModel(
        model_name="llama3.1",
        base_url="http://10.21.186.219:11434/api/chat"
    )

    try:
        response = model.generate_string("Hi! How are you?")
        print(f"Model response: {response}")
    except Exception as e:
        print(f"Error: {e}")
