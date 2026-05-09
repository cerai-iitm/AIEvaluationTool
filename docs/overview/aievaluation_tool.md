# AI Evaluation Tool

The AI Evaluation Tool is the core framework in this repository. It is designed to automate the evaluation of conversational AI systems across diverse real-world scenarios, target interfaces, and quality dimensions.

It helps teams verify, test, and benchmark conversational agents deployed as APIs, WhatsApp bots, and web applications. Instead of treating evaluation as an isolated manual activity, the platform provides a structured workflow for preparing test data, executing interactions, analyzing responses, and producing reports that support engineering, quality, and product decisions.

## Platform Summary

AIEvaluationTool is an end-to-end evaluation system for conversational AI. It connects test data, execution orchestration, model-based assessment, and result reporting into one workflow.

At a high level, it supports:

- importing structured test data and evaluation metadata
- executing prompts against target systems
- collecting and storing responses
- analyzing outputs with rule-based and model-based strategies
- generating structured evaluation reports

This makes it useful for both regular regression testing and deeper benchmarking exercises.

## Target Audience

- AI and ML engineers developing and deploying conversational AI systems
- QA teams responsible for chatbot and assistant validation
- product managers evaluating model behavior before production rollout
- compliance and governance stakeholders reviewing responsible AI behavior

## Key Use Cases

- Automated testing of conversational agents across multiple platforms
- Performance benchmarking against predefined quality metrics
- Safety and toxicity evaluation of generated responses
- Multilingual capability assessment
- Compliance and responsible AI verification

## Core Benefits

- Automated testing reduces reliance on manual prompt-by-prompt validation.
- Comprehensive evaluation spans quality, safety, language, performance, and privacy dimensions.
- The end-to-end pipeline connects execution, analysis, and reporting in one workflow.
- LLM-as-judge support enables richer evaluation than rule-based scoring alone.
- Multi-platform support allows the same framework to be used across API, WhatsApp, and web deployments.
- Detailed reports help teams identify both strengths and failure patterns.

## Evaluation Areas

The platform is organized around a set of evaluation areas that together provide a balanced view of conversational AI behavior. Instead of focusing only on correctness, these areas help teams assess trustworthiness, usability, robustness, multilingual performance, and operational reliability.

- **Responsible AI** - focuses on fairness, bias, truthfulness, robustness, transparency, explainability, and cultural sensitivity in model behavior.
- **Conversational Quality** - examines coherence, fluency, relevance, lexical richness, and the overall quality of the response as a natural conversation.
- **Guardrails And Safety** - evaluates how the system responds to harmful, toxic, adversarial, hallucinated, or out-of-scope inputs, including refusal behavior and content filtering.
- **Language Support** - measures multilingual capability with particular attention to Indian languages, transliteration handling, mixed-language contexts, and fluency across language boundaries.
- **Task Performance Metrics** - focus on whether the system completes the intended task accurately, consistently, and in a way that aligns with the expected outcome.
- **Performance And Scalability** - cover latency, throughput, uptime, failure behavior, and reliability under load.
- **Privacy And Safety** - examine misuse resistance, jailbreak handling, exaggerated safety behavior, privacy awareness, and privacy leakage.

## Supported Target Types

- API
- WhatsApp
- Web Application

The same framework can therefore be applied to different deployment environments without changing the overall evaluation model.

## System Architecture

AIEvaluationTool follows a modular, layered architecture designed for scalability and extensibility.

![System Architecture](../../screenshots/Arch.jpg)

## Core Components

### Data

The data layer stores testcases, configurations, strategy mappings, and evaluation results. It uses either MariaDB or SQLite, depending on the deployment scenario and scale.

Main characteristics:

- centralized storage for evaluation data and results
- JSON-based inputs for plans, strategies, defaults, and mappings
- reusable structured assets for repeated evaluation runs

### Execution

The execution layer is responsible for sending prompts to target systems and collecting responses.

Key parts:

- **Test Case Executor** distributes and executes testcases across supported target types
- **Interface Manager** automates interactions with APIs, WhatsApp flows, and web applications using Selenium and ChromeDriver where needed

### Analysis

The analysis layer applies evaluation logic to collected responses.

Key parts:

- **Response Analyzer** processes outputs after execution
- **Strategy Engine** applies model-based and rule-based evaluators
- **LLM-as-Judge** supports richer qualitative scoring where appropriate

### Integration

The integration layer connects the platform to model-serving systems and external services.

Key parts:

- **Sarvam AI Service** hosts specialized models for generation, translation, and safety analysis
- **External APIs** can be used for toxicity scoring or cloud-based language model access

### Management

The management layer supports structured control over data and access.

Key parts:

- **TDMS** provides the web-based system for managing test data and related assets
- **ORM** provides an abstraction layer for database interaction and entity modeling

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI |
| **Database** | MariaDB or SQLite |
| **Frontend** | Node.js 20.19+ or 22.14+ |
| **Web Automation** | ChromeDriver, Chrome/Chromium Browser |
| **ML/AI Models** | Ollama, Hugging Face Transformers, OpenAI API |
| **APIs** | RESTful services, OpenAI-compatible endpoints |

## Key Dependencies

- `selenium` for web and WhatsApp automation
- `pydantic` for data validation and modeling
- `fastapi` for API services
- `requests` for HTTP communication
- `transformers` for Hugging Face model integration
- `ollama` for local LLM deployment

## Repository Layout

The repository is organized to separate data, application modules, shared libraries, and configuration.

```text
AIEvaluationTool/
├── data/
│   ├── DataPoints.json
│   ├── plans.json
│   ├── strategy_map.json
│   ├── strategy_id.json
│   ├── metric_strategy_mapping.json
│   └── defaults.json
│
├── src/
│   ├── app/
│   │   ├── importer/
│   │   │   ├── main.py
│   │   │   └── config.json
│   │   ├── interface_manager/
│   │   │   ├── main.py
│   │   │   ├── credentials.json
│   │   │   └── xpaths.json
│   │   ├── testcase_executor/
│   │   │   ├── main.py
│   │   │   └── config.json
│   │   ├── response_analyzer/
│   │   │   ├── analyze.py
│   │   │   ├── report.py
│   │   │   └── config.json
│   │   ├── sarvam_ai/
│   │   │   └── main.py
│   │   ├── maintenance/
│   │   │   ├── config.json
│   │   │   └── fix_language.py
│   │   ├── prompt_quality_evaluation_tool/
│   │   │   ├── main.py
│   │   │   ├── API_keys.json
│   │   │   └── metric_and_submetric.xlsx
│   │   ├── TDMS/
│   │   │   ├── back-end/
│   │   │   │   ├── main.py
│   │   │   │   └── database/
│   │   │   └── front-end/
│   │   └── TestCaseExecutorDashboard/
│   │       ├── back-end/
│   │       │   ├── .env
│   │       │   ├── .env.example
│   │       │   ├── main.py
│   │       │   └── config.json
│   │       └── front-end/
│   └── lib/
│       ├── strategy/
│       │   ├── .env
│       │   └── .env.example
│       ├── orm/
│       ├── data/
│       ├── interface_manager/
│       │   └── client.py
│       └── utils/
├── requirements.txt
├── .env.example
└── README.md
```

## Module Descriptions

### `data/`

This directory contains core evaluation assets such as test datasets, plan definitions, strategy mappings, and default values.

Typical contents include:

- Testcase datasets
- Strategy and metric mappings
- Default configuration values

### `src/app/`

This area contains the main application modules.

- `importer/` loads JSON data into the database
- `interface_manager/` manages interactions with supported target platforms
- `testcase_executor/` orchestrates testcase execution
- `response_analyzer/` evaluates collected responses
- `sarvam_ai/` serves specialized AI models used by evaluation strategies
- `TDMS/` provides the test data management system
- `prompt_quality_evaluation_tool/` provides prompt-focused evaluation workflows
- `TestCaseExecutorDashboard/` provides the web UI for execution monitoring and review
- `maintenance/` contains cleanup and maintenance utilities

### `src/lib/`

This area contains reusable libraries and shared code.

- `strategy/` holds evaluation strategy implementations
- `orm/` provides database abstraction and entity modeling
- `data/` contains Pydantic data models
- `interface_manager/` provides a client for communicating with Interface Manager
- `utils/` contains shared helper functions

## Ecosystem Context

The AI Evaluation Tool is the center of the repository’s larger ecosystem. It works alongside:

- **Docker Setup** for containerized execution
- **TDMS** for managing evaluation data
- **PQET** for prompt-focused evaluation
- **AI Evaluation Tool UI** for run monitoring and review

Together, these pieces support a complete evaluation lifecycle, from prompt and testcase preparation to execution, analysis, and reporting.

## Related Sections

- [AI Evaluation Tool CLI](../ai_evaluation_tool_cli/index.md)
- [Docker Setup](../docker_setup/index.md)
- [TDMS + Dashboard UI](../TDMS_and_Dashboard_ui/index.md)
- [PQET](../pqet/index.md)
- [TDMS + Dashboard UI](../TDMS_and_Dashboard_ui/index.md)
