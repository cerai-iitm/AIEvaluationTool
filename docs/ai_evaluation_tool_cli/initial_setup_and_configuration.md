# Initial Setup And Configuration

This page covers everything required before running the AI Evaluation Tool from the command line: system prerequisites, repository setup, database preparation, the shared CLI configuration, environment variables, XPath and credentials, and target registration.

## System Requirements

### Hardware Requirements

- Minimum `8 GB` RAM
- `24 GB+` RAM recommended for local LLM deployment
- Multi-core CPU with at least `4` cores
- `50 GB+` free disk space for models and databases
- NVIDIA-compatible GPU recommended for faster inference

### Software Requirements

- Linux only.
- `Python 3.10+`
- `Node.js 20.19+` or `22.12+`
- `MariaDB Server 10.5+` if using MariaDB
- Latest Google Chrome
- Matching ChromeDriver version
- `Ollama` for local LLM serving
- GPU drivers when running accelerated inference

## Install MariaDB

Skip this section if you are using SQLite.

On Ubuntu, install MariaDB Server and the Python connector dependency:

```bash
sudo apt update
sudo apt install mariadb-server libmariadb-dev
```

Then install the Python connector in the same Python environment used for the backends:

```bash
pip install mariadb
```

  > Note - Check the official MariaDB documentation for any changes to packages or installation instructions before proceeding.

## Clone The Repository

```bash
git clone https://github.com/cerai-iitm/AIEvaluationTool
cd AIEvaluationTool
```

## Create A Python Virtual Environment

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Install ChromeDriver

ChromeDriver is required for web and WhatsApp automation. Install the ChromeDriver version that matches your installed Chrome browser.

## Database Setup

### SQLite

SQLite can be used as the default database for smaller development workflows.

### MariaDB

Use MariaDB for larger datasets or multi-user environments.

```bash
mysql -u root -p
```

```sql
CREATE DATABASE aievaluationtool;
CREATE USER 'aiet_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON aievaluationtool.* TO 'aiet_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Node.js Dependencies

The CLI workflow itself is Python-first, but parts of the repository also rely on Node.js. Ensure Node.js `20.19+` or `22.12+` is available on the system when working with the repository.

## Strategy Environment File

Create the strategy environment file from the example:

```bash
cp src/lib/strategy/.env.example src/lib/strategy/.env
```

## Prepare Data Files

Ensure the `data/` directory includes the evaluation assets referenced by the shared `config.json`:

- `plans.json`
- `updated_datapoints.json`
- `strategy_map.json`
- `strategy_id.json`
- `metric_strategy_mapping.json`

If your local config points to a different testcase file such as `DataPoints.json`, keep the `files.testcases` value aligned with that file.

More detailed seeded datapoints may be maintained separately and added as needed.

## Configure The Shared CLI Config

The importer, testcase executor, response analyzer, and report generator all use the repository-level `config.json`.

Path:

- `config.json`

Run the CLI commands from the repository root so the same config file works consistently across all stages.

Example structure:

```json
{
  "db": {
    "engine": "sqlite",
    "file": "AIEvaluationData.db",
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "jarvis2025",
    "database": "AIEvaluationData"
  },
  "files": {
    "plans": "data/plans.json",
    "testcases": "data/updated_datapoints.json",
    "strategies": "data/strategy_id.json"
  },
  "target": {
    "application_type": "WHATSAPP_WEB",
    "application_name": "Vaidya AI",
    "application_url": "https://web.whatsapp.com/",
    "agent_name": "Vaidya AI"
  },
  "interface_manager": {
    "docker": false,
    "base_url": "http://localhost:8000"
  }
}
```

### What Each Section Is Used For

- `db`: Shared database settings used by importer, testcase executor, response analyzer, and report generation.
- `files`: Input JSON assets used by the importer.
- `target`: Target selection used during testcase execution.
- `interface_manager`: Interface Manager connection details used by the testcase executor.

## Configure Root Environment Variables

Create a root `.env` file from `.env.example` and set the model and API values required by your strategy configuration.

Example:

```env
OLLAMA_URL="http://localhost:11434"
GPU_URL="http://localhost:8000"
LLM_AS_JUDGE_MODEL="qwen3:32b"
PERSPECTIVE_API_KEY="your_perspective_api_key"
SARVAM_API_KEY="your_sarvam_api_key"
GEMINI_API_KEY="your_gemini_api_key"
OPENAI_API_KEY="your_openai_api_key"
```

### Variable Meaning

- `OLLAMA_URL` points to the Ollama endpoint used by local LLM-based strategies.
- `GPU_URL` points to the Sarvam AI REST API service or another inference endpoint.
- `LLM_AS_JUDGE_MODEL` defines the default judge model.
- `PERSPECTIVE_API_KEY`, `SARVAM_API_KEY`, `GEMINI_API_KEY`, and `OPENAI_API_KEY` enable API-backed strategies.

## Configure XPath And Credentials

For web and WhatsApp targets, configure the Interface Manager support files:

- `src/app/interface_manager/xpaths.json`
- `src/app/interface_manager/credentials.json`

### XPath Guidance

- inspect the target application in the browser
- copy the XPath for login, logout, prompt entry, and response elements
- prefer stable relative XPath expressions over brittle absolute ones

Example `xpaths.json` structure:

```json
{
  "applications": {
    "app_name_here": {
      "LoginPage": {
        "email_input": "xpath_for_email_input",
        "password_input": "xpath_for_password_input",
        "login_button": "xpath_for_login_button"
      },
      "LogoutPage": {
        "profile": "xpath_for_profile_icon",
        "logout_button": "xpath_for_logout_button"
      },
      "ChatPage": {
        "contact_search": "xpath_for_contact_search",
        "prompt_input": "xpath_for_prompt_input",
        "agent_response": "xpath_for_agent_response",
        "message_in": "xpath_for_incoming_message",
        "message_out": "xpath_for_outgoing_message"
      },
      "OtherPages": {
        "custom_element_1": "xpath_for_custom_element",
        "custom_element_2": "xpath_for_custom_element"
      }
    }
  }
}
```

Example `credentials.json` structure:

```json
{
  "applications": {
    "cpgrams": {
      "username": "user_cpgrams",
      "password": "pass_cpgrams"
    },
    "openweb-ui": {
      "username": "user_openweb_ui",
      "password": "pass_openweb_ui"
    }
  }
}
```

## Register The Target Application

Supported target types:

- `API`
- `WhatsApp`
- `WebApp`

The `target.application_name` in the shared `config.json` should match a target already present in the database.

If your workflow requires manual target registration in the importer path, use the following structure:

```python
tgt = Target(
    target_name="your_agent_name",
    target_type="API",
    target_url="https://your-api-endpoint.com",
    target_description="Your agent description",
    target_domain="Healthcare",
    target_languages=["english"]
)

target_id = db.add_or_get_target(target=tgt)
```

## Related Repository Configuration

The README also includes related configuration for adjacent systems in the same repository:

- `src/app/TDMS/back-end/database/config.json`
- `src/app/TestCaseExecutorDashBoard/back-end/config.json`

Those files are not part of the core CLI flow that uses the shared repository-level `config.json`, but they matter if you are using TDMS or the web dashboard alongside the CLI pipeline.

## Quick Readiness Checklist

- Repository cloned
- Python environment created
- Dependencies installed
- Chrome and ChromeDriver aligned
- Database configured
- Shared `config.json` updated
- `.env` created
- Strategy `.env` created
- XPath and credentials configured
- Target details prepared
- Data files present
