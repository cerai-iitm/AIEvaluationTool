import json
import pandas as pd
from googletrans import Translator
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import os
from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
import language_tool_python
from dotenv import load_dotenv
import time
import asyncio

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts.prompt import PromptTemplate

from opik.integrations.langchain import OpikTracer
from opik.evaluation.metrics import GEval
from opik import Opik
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
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

embedding_model = SentenceTransformer("thenlper/gte-small")

async def language_coverage(prompts, test_case_responses):
    """
    Strategy 1
    Calculate the language coverage of the response using language detection.
    """
    result = []
    async with Translator() as translator:
        for i in tqdm(range(len(prompts))):
            response_language = await translator.detect(test_case_responses[i])
            prompt_language = await translator.detect(prompts[i])
            if response_language.lang == prompt_language.lang:
                result.append(1.0)
            else:
                result.append(0.0)

    print("Language Coverage:", (sum(result) / len(result))*100, "%" )

async def language_coverage_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 2
    Calculate the language coverage of the response by bringing the langauges to the same plane.
    This is done by translating the response to a single language ie English and then checking if they match.
    """
    result = []
    translator = Translator()
    for i in tqdm(range(len(prompts))):
            response_language = await translator.translate(test_case_responses[i], dest='en')
            prompt_language = await translator.translate(prompts[i], dest='en')
            expected_response_language = await translator.translate(expected_responses[i], dest='en')
            embeddings = embedding_model.encode([response_language.text,prompt_language.text, expected_response_language.text], show_progress_bar=True)
            similarity = cos_sim(embeddings[0], embeddings[1])
            similarity_2 = cos_sim(embeddings[1], embeddings[2])
            print("Similarity:", similarity)
            if similarity > 0.8 or similarity_2 > 0.8:
                result.append(1.0)
            else:
                result.append(0.0)

    print("Language Coverage Similarity:", (sum(result) / len(result))*100, "%" )

def text_similarity(prompts, test_case_responses, expected_responses):
    """
    Strategy 4
    Use text similarity to check if the response matches the prompt.
    """
    result = []
    for i in tqdm(range(len(prompts))):
        print(prompts[i])
        print(test_case_responses[i])
        print(expected_responses[i])
        embeddings = embedding_model.encode([prompts[i],test_case_responses[i], expected_responses[i]])
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

def grammarChecker(text):
    tool = language_tool_python.LanguageTool('en-US')
    result = tool.check(text)
    return result

def grammarcheck(test_case_responses):
    translator = Translator()
    result = []
    for i in test_case_responses:
        print(i)
        response_language = translator.detect(i).lang
        if response_language != "en":
            response_translation = translator.translate(i, dest='en').text
        else:
            response_translation = i
        grammar_check = grammarChecker(response_translation)
        if len(grammar_check) > 1:
            result.append(0)
        else:
            result.append(1)
    print("Grammar Result:", (sum(result) / len(result))*100, "%" )

def llm_as_judge(metric_name,task_intro,judge_prompt, system_prompt, prompts, test_case_response, expected_response):
    """
    Strategy 3
    Use an LLM to judge the language coverage of the response.
    """
    result = []
    metric = GEval(
            name=metric_name,
            task_introduction=task_intro,
            evaluation_criteria=judge_prompt,
            model=llm)
    for i in tqdm(range(len(prompts))):
        score = metric.score(
                input=prompts[i],
                output=test_case_response,
                expected_output=expected_response,
                context=system_prompt
            )
        result.append(score.value)
    print("LLM as Judge Score:", (sum(result) / len(result))*100, "%" )

# if __name__ == "__main__":
start_time = time.time()
# grammarcheck(["i wait for my firend", "he are super boyz"])
new_prompts = []
test_case_responses = []
for i in range(len(prompts)):
    new_prompts.append(prompts[i]["Prompt"])
    test_case_responses.append(chats[i]["TestCaseResponse"])
#asyncio.run(language_coverage(new_prompts, test_case_responses))
asyncio.run(language_coverage_similarity(new_prompts, test_case_responses, test_case_responses))
#text_similarity(new_prompts, test_case_responses, test_case_responses)
# toxicity_model_result(test_case_responses)
# grammarcheck(test_case_responses)
end_time = time.time()
print("Time taken by the process-", end_time-start_time, " s")
