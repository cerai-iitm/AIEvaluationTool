# AI Evaluation Tool

## Overview

A comprehensive evaluation framework designed to rigorously test and validate the performance, consistency, and reliability of conversational AI systems across diverse use cases and scenarios.

## Description

The Conversational AI Evaluation Tool is a comprehensive and scalable framework designed to rigorously assess the performance, reliability, and safety of conversational AI systems. Tailored for developers, researchers, and QA teams, the tool enables automated, systematic evaluation of dialogue agents across a wide range of metrics including Inclusivity, Transparency, Explainability, Cultural Sensitivity, Dialogue Coherence, Language Coverage, Functional Domain Relevance and more.

## Getting started

## Prerequistes
- Python 3.9 or greater
- Chrome Web Driver (Download and install chromedriver from <a href="https://googlechromelabs.github.io/chrome-for-testing/">here</a> based on your OS (eg. Windows, Linux, or Mac OS))

## Setting up

1. Clone the Repository:

```bash
git clone https://github.com/cerai-iitm/AIEvaluationTool.git
cd AIEvaluationTool
```
2. Install python package dependencies with the following command:

```bash
pip install -r requirements.txt
```

3. Directory Structure

```bash
AIEvaulationTool
├── Data
│   ├── DataPoints.json
│   ├── Dataset_Evaluation.csv
│   ├── plans.json
│   ├── response_analysis_output.json
│   ├── responses.json
│   └── strategy_map.json
├── InterfaceManager
│   ├── APIService
│   │   ├── docker
│   │   │   └── Dockerfile
│   │   ├── README.md
│   │   └── src
│   │       ├── config.json
│   │       ├── logger.py
│   │       ├── main.py
│   │       ├── openui.py
│   │       ├── routers
│   │       │   ├── chat_router.py
│   │       │   └── common.py
│   │       └── whatsapp.py
│   ├── ClientLibrary
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── src
│   │       └── InterfaceManagerClient.py
│   └── __init__.py
├── ResponseAnalyzer
│   └── src
│       ├── display_tabulate.py
│       ├── ResponseAnalyzer.py
│       └── strategies.py
├── TestCaseExecutionManager
│   ├── README.md
│   └── src
│       └── TestCaseExecutionManager.py
├── README.md
└── requirements.txt

13 directories, 27 files

```

## Usage

### Command to run the TestCase Execution Manager

Run the AI Evaluation Tool Server with the following command,

```bash
python InterfaceManager/APIService/src/main.py
```

### Command to run the TestCaseExecution Manager

Run the TestCase Execution Manager with the following command,

```bash
python TestCaseExecutionManager/src/TestCaseExecutionManager.py --test_plan_id <plan-id> --test_case_count <number of prompts>
```

For example,

```bash
python TestCaseExecutionManager/src/TestCaseExecutionManager.py --test_plan_id T2 --test_case_count 5
```

### Command to run the ResponseAnalyser 

```bash
 python -W ignore ResponseAnalyzer/src/ResponseAnalyzer.py
```

## Sample Screenshots



