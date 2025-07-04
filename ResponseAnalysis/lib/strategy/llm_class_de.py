from langchain_ollama import ChatOllama
from deepeval.models.base_model import DeepEvalBaseLLM

class OllamaGPU(DeepEvalBaseLLM):
    def __init__(
        self,
        model
    ):
        self.model = model

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        return chat_model.invoke(prompt)

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return "Custom Ollama Model"

# Replace these with real values
custom_model = ChatOllama(
    model = "mistral",
    temperature = 0.9,
    base_url="http://10.21.186.219:11434"
)
ollama_model = OllamaGPU(model=custom_model)
print(ollama_model.generate("Write me a joke"))