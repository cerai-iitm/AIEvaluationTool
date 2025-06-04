import os
import json
from strategies import (
    language_coverage,
    language_coverage_similarity,
    llm_as_judge,
    text_similarity,
    toxicity_model_result,
    grammarcheck,
    lexical_diversity,
    bleu_score_metric,
    meteor_metric,
    rouge_score_metric)

with open('Data/DataPoints.json', 'r') as file:
    datapoints = json.load(file)

with open('Data/plans.json', 'r') as file:
    plans = json.load(file)

with open('Data/responses.json', 'r') as file:
    responses = json.load(file)

with open('Data/strategy_map.json', 'r') as file:
    strat_map = json.load(file)

