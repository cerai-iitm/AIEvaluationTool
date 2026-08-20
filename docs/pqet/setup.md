# PQET Setup

Use this page to launch the Prompt Quality Evaluation Tool locally.

## Prerequisites

- Python dependencies installed from the repository root:

```bash
pip install -r requirements.txt
```

## Configure Gemini API Keys

PQET calls the Gemini API directly and rotates across a pool of keys. Before starting the app, edit [`src/app/prompt_quality_evaluation_tool/API_keys.json`](../../src/app/prompt_quality_evaluation_tool/API_keys.json) and replace the placeholder values with real Gemini API keys:

```json
{
  "GEMINI_API_KEYS": [
    "your-gemini-api-key-1",
    "your-gemini-api-key-2"
  ]
}
```

At least one valid key is required. The app reads this file relative to its own directory, so it must exist before starting.

## Start The Application

```bash
cd src/app/prompt_quality_evaluation_tool
streamlit run main.py
```

After the command starts the application, open the local URL shown in the terminal, typically on port `8501`.

## Notes

- The metric/submetric definitions shown in the UI come from the bundled `metric_and_submetric.xlsx` file in the same directory.
- Evaluation results are shown in the UI only and are not persisted anywhere.
- PQET is intended for prompt-focused evaluation rather than full end-to-end execution workflows.
