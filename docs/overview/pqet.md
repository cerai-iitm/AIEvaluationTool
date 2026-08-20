# PQET

The Prompt Quality Evaluation Tool, or PQET, is the part of the ecosystem focused specifically on prompt quality and expected-response quality.

## What PQET Does

PQET is designed to evaluate prompts before or alongside broader system-level evaluation. Rather than focusing on full end-to-end target execution, it concentrates on the quality of prompts, expected responses, and the metric structure used to judge them.

## Why It Matters

Prompt quality has a direct effect on downstream evaluation quality. If prompts are weak, unclear, or poorly aligned with the intended metrics, the larger evaluation pipeline becomes less reliable. PQET helps teams inspect prompt quality earlier and more deliberately.

## Main Capabilities

- prompt and expected-response quality assessment
- metric and submetric driven review
- LLM-assisted evaluation workflows
- interactive usage through a Streamlit interface

This makes PQET especially useful for teams refining datasets, improving test quality, or validating prompts before scaling into larger execution runs.

## Architecture Summary

PQET is organized as a lightweight, stateless application with:

- Streamlit UI
- Python-based evaluation logic
- Metric/submetric definitions loaded from a bundled Excel file (`metric_and_submetric.xlsx`)
- Gemini API calls (with API-key rotation) for LLM-assisted scoring
- No persistence: evaluation results are shown in the UI only and are not saved

## How PQET Fits Into The Ecosystem

PQET complements the broader AI Evaluation Tool workflow. The main platform handles end-to-end execution and response analysis, while PQET focuses earlier in the lifecycle on the quality of the prompt design itself.

## Typical Use Cases

- reviewing prompts before execution at scale
- validating expected responses and scoring structure
- identifying weak or ambiguous prompts
- improving prompt datasets iteratively

## Related Sections

- [PQET documentation](../pqet/index.md)
- [AI Evaluation Tool CLI](../cli/index.md)
