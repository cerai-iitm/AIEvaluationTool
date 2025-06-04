import os


with open('Data/metric_operation.json', 'r') as file:
    metrics = json.load(file)

with open('Data/chat_execution.json', 'r') as file:
    chat_exec = json.load(file)

with open('Data/prompts.json', 'r') as file:
    prompts = json.load(file)

with open('Data/chats.json', 'r') as file:
    chats = json.load(file)