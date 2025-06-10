# AIEvaluationTool
A comprehensive evaluation tool for verifying conversational AI applications.

This project offers a robust, end-to-end framework for evaluating the performance and reliability of conversational AI systems across a variety of real-world scenarios and quality metrics. The AIEvaluationTool is designed to automate the process of testing, analyzing, and benchmarking conversational agents, ensuring they meet high standards of accuracy, safety, and user experience.

## Directory Structure

```
AIEvaluationTool/
├── Data/
│   ├── DataPoints.json
│   ├── plans.json
│   ├── strategy_map.json
│   └── ...
├── InterfaceManager/
│   ├── APIService/
│   │   ├── src/
│   │   │   └── ... (API source code)
│   │   └── requirements.txt
│   └── ... (other interface-related modules)
├── ResponseAnalyzer/
│   ├── src/
│   │   └── ... (analysis scripts)
│   └── requirements.txt
├── TestCaseExecutionManager/
│   ├── src/
│   │   └── ... (test execution scripts)
│   └── requirements.txt
```

## Key Features and Evaluation Dimensions:

- **Responsible AI**: Assesses the ethical and safe behavior of the AI, including toxicity detection and guardrail enforcement.

- **Conversational Quality**: Measures the fluency, coherence, and appropriateness of responses using advanced linguistic metrics and human-like judgment.

- **Guardrails and Safety**: Evaluates the AI's ability to avoid generating unsafe, toxic, or inappropriate content, and to comply with predefined safety and ethics.

- **Language Support**: Evaluates the model's ability to understand and generate text in multiple languages, including coverage and similarity metrics.

- **Task Understanding**: Tests the AI's ability to comprehend and execute user instructions accurately.

- **Business Requirements Alignment**: Ensures the AI's responses align with specific business goals and compliance needs.

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

- **Python 3.8+**
- **Google Chrome Browser**
- **ChromeDriver** (must match your Chrome version; this is a mandatory install for interface automation)

---

### 3. **Install Python Dependencies**

Install all dependencies for each component using the provided `requirements.txt` files:

```bash
# For Response Analysis
pip install -r ResponseAnalyzer/src/requirements.txt

# For API Service and Interface Interaction
pip install -r InterfaceManager/APIService/requirements.txt

# For Test Case Execution Manager
pip install -r TestCaseExecutionManager/requirements.txt
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

Ensure the `Data/` directory contains the following files (already present in the repository):
- `DataPoints.json`
- `plans.json`
- `strategy_map.json`
- (Other .csv/.tsv files are generated during runs)

---

## Running the Evaluation Pipeline

**Step 1: Start the InterfaceManager API Service**

Open a terminal on your machine and run:
```bash
cd InterfaceManager/APIService/src 
python main.py
```

#### API Server Running

After starting the InterfaceManager API Service, the terminal shows the following outputs.

![Interface Server Setup](screenshots/API_Server_load.jpg)
![Interface Server Running](screenshots/API_Server_running.jpg)

**Step 2: Run the Test Case Execution Manager**

Open another new terminal on your machine and run:
```bash
cd TestCaseExecutionManager/src
python TestCaseExecutionManager.py --test_plan_id <test_plan_id> --test_case_count <test_case_count>
```
*(Adjust `--test_plan_id` and `--test_case_count` as needed.)*

#### Test Case Execution Manager Running
On running the Test Case Execution Manager, the terminal output should look similar to:

![TEM Launch](screenshots/TestCaseExecutionManager.jpg)
![TEM Running](screenshots/TEM_Running.jpg)

The Test Case Execution Manager leverages the interface automation to automatically deliver test cases to the conversational platform and retrieve responses without manual intervention.

![Interface](screenshots/Interface.jpg)


This step will execute the test cases and store the responses in `Data/responses.json`.

**Step 3: Run the Response Analyzer**

**Once the previous step has completed and `responses.json` is populated**, open a new terminal and run:

```bash
cd ResponseAnalyzer/src
python -W ignore ResponseAnalyzer.py
```

> **Note:** If you are using a local model (e.g., Ollama or any OpenAI-compatible local model), ensure that the model server is running in the background and accessible before executing the Response Analyzer.

#### Response Analyzer Running

![Response Analyzer Running](screenshots/Response_Analyzer.jpg)

This sequence will:
- Start the API server for interface management.
- Execute test cases and store responses in `Data/responses.json`.
- Analyze the stored responses and generate evaluation reports.

---

## Results

The Response Analyzer block when executed will display a detailed report on the terminal, showing scores evaluated for metrics under the test plan and can be used as an indicator of the validity of the model against a particular metric.

#### Evaluation Report
A sample evaluation report generated by the Response Analyzer can be seen below:

![Evaluation Report](screenshots/Report_Generated.jpg)

---

