# AI Evaluation Tool CLI

This section documents the full command-line workflow for the AI Evaluation Tool in a format suited for an official documentation website. It brings together installation, configuration, GPU and model setup, execution, analysis, and reporting.

The CLI pipeline uses a single shared repository-level `config.json` for importer, testcase execution, response analysis, and report generation.

## What This Section Covers

- local prerequisites and environment preparation
- configuration of the shared `config.json`, credentials, and environment variables
- local and remote GPU-backed model setup
- importer and testcase executor workflow
- response analysis and report generation

## Chapters

- [Initial Setup and Configuration](./initial_setup_and_configuration.md)
- [GPU Setup](./gpu_setup.md)
- [Importer and Testcase Execution](./importer_and_testcase_execution.md)
- [Analysis and Report](./analysis_and_report.md)

## End-to-End Flow

- Install system prerequisites and repository dependencies.
- Configure the shared `config.json`, environment variables, XPath mappings, and credentials.
- Prepare model endpoints, either locally or on a remote GPU host.
- Import data and register the target application.
- Start Interface Manager and execute test cases.
- Analyze collected responses.
- Generate the final evaluation report.

## Supported Target Types

- API
- WhatsApp
- Web Application

## Core CLI Components

- `src/app/importer`
- `src/app/interface_manager`
- `src/app/testcase_executor`
- `src/app/response_analyzer`
- `src/app/sarvam_ai`
- `src/lib/strategy`

## Related References

- [Initial Setup and Configuration](./initial_setup_and_configuration.md)
- [GPU Setup](./gpu_setup.md)
- [Importer and Testcase Execution](./importer_and_testcase_execution.md)
- [Analysis and Report](./analysis_and_report.md)
