'''from deepeval.models import DeepEvalBaseLLM
from langchain_community.llms import Ollama
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

class OllamaLLM(DeepEvalBaseLLM):
    def __init__(self, model_name="mistral:7b-instruct", temperature=0, base_url="http://10.21.186.219:11434"):
        self.model_name = model_name
        self.temperature = temperature
        self.base_url = base_url

    def load_model(self):
        return Ollama(model=self.model_name, temperature=self.temperature, base_url=self.base_url)

    def generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        return chat_model.invoke(prompt)

    async def a_generate(self, prompt: str) -> str:
        chat_model = self.load_model()
        return await chat_model.ainvoke(prompt)

    def get_model_name(self):
        return self.model_name

if __name__ == "__main__":
    ollama_llm = OllamaLLM(model_name="mistral:7b-instruct", base_url="http://10.21.186.219:11434")

    criteria = "Coherence (1-5) - the collective quality of all sentences. We align this dimension with the DUC quality question of structure and coherence whereby the summary should be well-structured and well-organized. The summary should not just be a heap of related information, but should build from sentence to sentence to a coherent body of information about a topic."

    coherence_metric = GEval(
        name="Coherence",
        criteria=criteria,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=ollama_llm
    )

    test_case = LLMTestCase(
        input="Hey how's the weather like today?",
        actual_output="It's alright!",
        expected_output="The weather is fine today."
    )

    coherence_metric.measure(test_case)
    print(coherence_metric.score, coherence_metric.reason)'''


"""from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_id = "mistralai/Mistral-7B-Instruct-v0.2"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
output = pipe("What is the capital of France?", max_new_tokens=20)
print(output[0]['generated_text'])"""


import requests
import time

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "mistral"

prompt = "Explain black holes in simple terms."


def wait_for_ollama_server(timeout=60):
    for _ in range(timeout):
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            if response.status_code == 200:
                print(" Ollama server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        print(" Waiting for Ollama server to be available...")
        time.sleep(1)
    print("Ollama server did not respond in time.")
    return False

# Function to query Mistral
def query_model(prompt):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL_NAME, "prompt": prompt},
        stream=True
    )

    print(f"\n Response from {MODEL_NAME}:\n")
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"), end='')

if __name__ == "__main__":
    if wait_for_ollama_server():
        query_model(prompt)

