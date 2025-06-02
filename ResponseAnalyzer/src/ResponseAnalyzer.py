import json
import pandas as pd
from googletrans import Translator
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from tqdm import tqdm
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts.prompt import PromptTemplate
from opik.integrations.langchain import OpikTracer
from opik.evaluation.metrics import GEval
from opik import Opik
import os
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification

os.environ["OPIK_API_KEY"] = "DMoieFG7spXUk1KZnp7MVaccB" 
os.environ["OPIK_WORKSPACE"] = "iamnithyaramesh"
opik_tracer = OpikTracer()
model_name = "llama3.2:1b"
llm = OllamaLLM(model=model_name,callbacks=[opik_tracer])


with open('Data/metric_operation.json', 'r') as file:
    metrics = json.load(file)

with open('Data/chat_execution.json', 'r') as file:
    chat_exec = json.load(file)

with open('Data/prompts.json', 'r') as file:
    prompts = json.load(file)

with open('Data/chats.json', 'r') as file:
    chats = json.load(file)

# print("Prompt Check:", prompts[0]["Prompt"])

# data = pd.read_csv('Data/Dataset_Evaluation.csv')
# lang_cov = data[data["Metric"]=="Language coverage "]

embedding_model = SentenceTransformer("thenlper/gte-small")

def language_coverage(prompts, test_case_responses):
    """
    Strategy 1
    Calculate the language coverage of the response using language detection.
    """
    result = []
    for i in tqdm(range(len(prompts))):
            translator = Translator()
            response_language = translator.detect(test_case_responses[i]).lang
            prompt_language = translator.detect(prompts[i]).lang
            if response_language == prompt_language:
                result.append(1.0)
            else:
                result.append(0.0)

    print("Language Coverage:", (sum(result) / len(result))*100, "%" )

def language_coverage_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 2
    Calculate the language coverage of the response by bringing the langauges to the same plane.
    This is done by translating the response to a single language ie English and then checking if they match.
    """
    result = []
    for i in tqdm(range(len(prompts))):
            translator = Translator()
            response_language = translator.translate(test_case_responses[i], dest='en').text
            prompt_language = translator.translate(prompts[i], dest='en').text
            expected_response_language = translator.translate(expected_responses[i], dest='en').text
            embeddings = embedding_model.encode([response_language,prompt_language, expected_response_language], show_progress_bar=True)
            similarity = cos_sim(embeddings[0], embeddings[1])
            similarity_2 = cos_sim(embeddings[1], embeddings[2])
            print("Similarity:", similarity)
            if similarity > 0.8 or similarity_2 > 0.8:
                result.append(1.0)
            else:
                result.append(0.0)

    print("Language Coverage Similarity:", (sum(result) / len(result))*100, "%" )

def llm_as_judge(metric_name,task_intro,judge_prompt, prompts, test_case_response, expected_response):
    """
    Strategy 3
    Use an LLM to judge the language coverage of the response.
    """
    result = []
    metric = GEval(
            name=metric_name,
            task_introduction=task_intro,
            evaluation_criteria="Does the response match the prompt in terms of language?",
            llm=llm,
            judge_prompt=PromptTemplate.from_template(judge_prompt))
    for i in tqdm(range(len(prompts))):
        score = metric.score(
                input=prompts[i],
                output=test_case_response,
                expected_output=expected_response
            )
        result.append(score.value)
    print("LLM as Judge Score:", (sum(result) / len(result))*100, "%" )

def text_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 4
    Use text similarity to check if the response matches the prompt.
    """
    result = []
    for i in tqdm(range(len(prompts))):
        embeddings = embedding_model.encode([prompts[i],test_case_responses[i], expected_responses[i]], show_progress_bar=True)
        print("Similarity:", similarity)
        similarity = cos_sim(embeddings[0], embeddings[1])
        similarity_2 = cos_sim(embeddings[1], embeddings[2])
        print("Similarity:", similarity)
        if similarity > 0.8 or similarity_2 > 0.8:
            result.append(1.0)
        else:
            result.append(0.0)

    print("Text Similarity:", (sum(result) / len(result))*100, "%" )

def toxicity_model_result(test_case_responses):
    """
    Strategy 5
    Use a toxicity model to check if the response matches the prompt.
    """
    tokenizer = AutoTokenizer.from_pretrained("nicholasKluge/ToxicityModel")
    all_tokens = []
    for i in tqdm(range(len(test_case_responses))):
        tokens = tokenizer(test_case_responses, truncation=True, max_length=512, return_token_type_ids=False, return_tensors="pt", return_attention_mask=True)
        all_tokens.append(tokens)
    model = AutoModelForSequenceClassification.from_pretrained("nicholasKluge/ToxicityModel")
    model.eval()
    device = "cpu"
    model.to(device)
    result = []
    for token in all_tokens:
        score = model(**token)[0].item()
        print(f"Toxicity Score: {score:.3f}")
        if score < 0:
            result.append(-1.0)
        else:
            result.append(1.0)
    print("Toxicity Model Result:", (sum(result) / len(result))*100, "%" )

if __name__ == "__main__":
    # language_coverage_plane()
