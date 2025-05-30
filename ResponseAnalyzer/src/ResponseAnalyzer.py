import json
import pandas as pd
from googletrans import Translator

with open('Data/metric_operation.json', 'r') as file:
    metrics = json.load(file)

with open('Data/prompts.json', 'r') as file:
    prompts = json.load(file)

with open('Data/chats.json', 'r') as file:
    chats = json.load(file)

# print("Prompt Check:", prompts[0]["Prompt"])

# data = pd.read_csv('Data/Dataset_Evaluation.csv')
# lang_cov = data[data["Metric"]=="Language coverage "]

def language_coverage():
    """
    Calculate the language coverage of the response.
    """
    result = []
    for i in range(len(prompts)):
        translator = Translator()
        response_language = translator.detect(prompts[i]["Prompt"]).lang
        prompt_language = translator.detect(chats[i]["TestCaseResponse"]).lang
        if response_language == prompt_language:
            print("Response Language:", response_language, "Prompt Language:", prompt_language)
            result.append(1.0)
        else:
            result.append(0.0)

    print("Language Coverage:", sum(result) / len(result))

if __name__ == "__main__":
    language_coverage()
