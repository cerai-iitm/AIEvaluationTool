# AIEvaluationTool
A comprehensive evaluation tool for verifying conversational AI applications.

This project offers a robust, end-to-end framework for evaluating the performance and reliability of conversational AI systems across a variety of real-world scenarios and quality metrics. The AIEvaluationTool is designed to automate the process of testing, analyzing, and benchmarking conversational agents, ensuring they meet high standards of accuracy, safety, and user experience.

## Directory Structure

```
AIEvaluationTool/
├── data/
│   ├── DataPoints.json
│   ├── plans.json
│   ├── strategy_map.json
│   └── ...
├── src/
│   ├── app/sarvam_ai
│   │   └── ... (scripts to run LLMs locally)
│   ├── app/importer
│   │   └── ... (scripts to import data from json to the database)
│   ├── app/interface_manager
│   │   └── ... (scripts to interact with the whastapp web or web app bots)
│   ├── app/testcase_executor
│   │   └── ... (scripts to run testcase execution from the prompts stored in the database)
│   ├── app/response_analyzer
│   │   └── ... (scripts to analyse the collected response and computer score and store in the database)
│   ├── lib/strategy
│   │   └── ... (implementation of model and rules based evaluation strategies)
│   ├── lib/orm
│   │   └── ... (ORM implementation of the data model)
│   ├── lib/data
│   │   └── ... (Pydantic classes of all the data model objects)
│   ├── lib/interface_manager
│   │   └── ... (wrapper class to talk to the Interface Manager stub)
│   ├── lib/utils
│   │   └── ... (helper functions)
│   ├── notebooks
│   │   └── ... (Python notebooks)
└── requirements.txt
```

## Key Features and Evaluation Dimensions:

- **Responsible AI**: Assesses the ethical and safe behavior of the AI, including toxicity detection and guardrail enforcement.

- **Conversational Quality**: Measures the fluency, coherence, and appropriateness of responses using advanced linguistic metrics and human-like judgment.

- **Guardrails and Safety**: Evaluates the AI's ability to avoid generating unsafe, toxic, or inappropriate content, and to comply with predefined safety and ethics.

- **Language Support**: Evaluates the model's ability to understand and generate text in multiple languages, including coverage and similarity metrics.

- **Task Understanding**: Tests the AI's ability to comprehend and execute user instructions accurately.

- **Performance and Scalability**: Assesses the system’s speed, reliability, and stability through performance and scalability metrics.

- **Privacy and Security**: Assesses the system’s ability to safeguard sensitive information, maintain user trust, and resist misuse or adversarial manipulation while ensuring balanced and responsible handling of safety constraints.

## How It Works:

- **Test Case Execution**: A mechanism to send a diverse set of prompts to the conversational AI, simulating real user interactions across different platforms (e.g., WhatsApp, web interfaces).

- **Response Analysis**: Applies a suite of custom and standard evaluation strategies—including text similarity, grammar checking, toxicity analysis, and more—to each response.

- **Metric Aggregation**: Aggregates results into comprehensive reports, highlighting strengths and areas for improvement across all tested dimensions.

## Setup Guide

### 1. **Clone the Repository**

```bash
git clone https://github.com/cerai-iitm/AIEvaluationTool
cd AIEvaluationTool
```

---

### 2. **Install Prerequisites**

Before installing Python dependencies, ensure you have the following prerequisites installed on your system:

- **Python 3.10+**
- **Google Chrome Browser**
- **ChromeDriver** (must match your Chrome version; this is a mandatory install for interface automation)

---

### 3. **Install Python Dependencies**

Install all dependencies for each component using the provided `requirements.txt` files:

```bash
# For installing dependencies
pip install -r requirements.txt
```

---

### 4. **Model Setup for LLM-based Evaluation**

To use the LLM-as-a-judge mechanism for evaluation, you must have a language model available. You can either:
- **Run a model locally** (e.g., using Ollama, OpenAI-compatible local models, etc.), or
- **Provide API keys** for cloud-based models (e.g., OpenAI, Anthropic, etc.)

**Supported Models:**
- OpenAI GPT-3.5/4 (via API key)
- Anthropic Claude (via API key)
- Ollama (local)
- Any OpenAI-compatible local model

**Configuration:**
- For API-based models, set your API key in a `.env` file or as an environment variable (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).
- For local models, ensure the model server is running and accessible at the expected endpoint (see your model provider's documentation).

Ensure your model is accessible and properly configured before running the evaluation pipeline. Refer to the relevant documentation for your chosen model provider for setup instructions.

---

### 5. **Prepare Data Files**

Ensure the `data/` directory contains the following files (already present in the repository):
- `DataPoints.json` (sample test dataset)
- `plans.json`
- `strategy_map.json`
- `strategy_id.json`
- `metric_strategy_mapping.json`
- **A detailed set of Seeding data points shall be provided upon request.**

---

## Running the Evaluation Pipeline

**Step 1: Import datapoints into Database**

Open a terminal on your machine and run:

```bash
python3 src/app/importer/main.py --config "path to the config file"
```

Replace the host, port number, username, password, and database name in the `config.json` file. After running the importer script, the terminal shows the following outputs.

![Importing datapoints to database](screenshots/importing%20data%20to%20database.png)

**Step 2: Start the InterfaceManager API Service**

Open a terminal on your machine and run:
```bash
cd src/app/interface_manager
python main.py
```

#### API Server Running

After starting the InterfaceManager API Service, the terminal shows the following outputs.

![Interface Server Running](screenshots/interface_manager_running.png)

**Step 3: Run the Test Case Execution Manager**

Replace the host, port number, username, password, and database name in the `config.json` file. Open another new terminal on your machine and run to see what options are available in testcase executor:

```bash
cd src/app/testcase_executor
python main.py --config "path to config file" -h
```

![Arguments available in Testcase Executor](screenshots/arguments%20of%20testcase%20executor.png)

![Plans](screenshots/get_plans.png)

![Metrics](screenshots/get_metrics.png)


To run the Testcase execution, run the following command:

```bash
cd src/app/testcase_executor
python main.py --testplan-id <testplan-id> --testcase-id <testcase-id> --metric-id <metric-id> --max-testcases <max-testcases>  --config "path to config file" --execute 
```
*(Adjust `--testplan-id`, `--testcase-id`, `--metric-id`, `--max-testcases` and  as needed.)*

#### Test Case Execution Manager Running
On running the Test Case Execution Manager, the terminal output should look similar to:

![TEM Running](screenshots/Testcase_execution_manager_running.png)

The Test Case Execution Manager leverages the interface automation to automatically deliver test cases to the conversational platform and retrieve responses without manual intervention.

![Interface](screenshots/Interface.jpg)


This step will execute the test cases and store the responses in `data/responses.json`.

**Step 4: Run the LLMS in your GPUs**

In order for the evaluation framework to work we need to have 4 models to be in place - 

1. sarvamai/sarvam-2b-v0.5
2. google/shieldgemma-2b
3. sarvamai/sarvam-translate
4. mistral:7b-instruct (Default LLM as Judge)

```bash
cd src/app/sarvam_ai
python main.py
```

You need to port forward to facilitate the model to connect to your testing machine. You can use the command below -

```bash
ollama run mistral:7b-instruct
ssh gpu_machine_cred@machineIP -L testing_machine_ip:11434:localhost:11434 -L testing_machine_ip:8000:localhost:8000
```

Here in 11434 the LLM as Judge Model ie mistral:7b-instruct is hosted through ollama and 8000 is used to serve the other 3 models.

There are other small sized models which gets downloaded while running this application. The models are - 

1. amedvedev/bert-tiny-cognitive-bias
2. NousResearch/Minos-v1
3. LibrAI/longformer-harmful-ro
4. vectara/hallucination_evaluation_model
5. thenlper/gte-small
6. all-MiniLM-L6-v2
7. facebook/bart-large-cnn
8. nicholasKluge/ToxiGuardrail
9. paraphrase-multilingual-mpnet-base-v2

**Step 5: Run the Response Analyzer**

**Once the previous step has completed and `responses.json` is populated**, open a new terminal and run:

```bash
cd src/app/response_analyzer
python analyze.py --config "path to config file" --run-name <run-name>
```

*(Adjust `--run-name` as needed.)*

> **Note:** If you are using a local model (e.g., Ollama or any OpenAI-compatible local model), ensure that the model server is running in the background and accessible before executing the Response Analyzer.

#### Response Analyzer Running
![Response Analysis Image](screenshots/Response_analyzer_running.png)

---

## Results

The Response Analyzer block when executed will display a detailed report on the terminal, showing scores evaluated for metrics under the test plan and can be used as an indicator of the validity of the model against a particular metric.

**To see the evaluation report**, open a new terminal and run:

```bash
cd src/app/response_analyzer
python report.py --config "path to config file" --run-name <run-name>
```

*(Use the same run-name used in analysis step.)*

#### Evaluation Report
A sample evaluation report generated by the Response Analyzer can be seen below:

![Evaluation Report](screenshots/report_generation.png)
---

