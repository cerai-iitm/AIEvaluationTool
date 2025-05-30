import json
import pandas as pd

with open('Data/metrics.json', 'r') as file:
    metrics = json.load(file)

# print("Metrics:", metrics)
metric_id = 1

def language_coverage(response):
    
