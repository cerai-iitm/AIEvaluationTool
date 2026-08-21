# Overview

This section introduces the AI Evaluation Tool ecosystem and the major parts of the platform that support an end-to-end evaluation workflow.

The repository is organized around a practical pipeline for evaluating conversational AI systems. At a high level, the workflow starts with test data preparation, moves through target interaction and execution, then continues into response analysis and final reporting. Around that core workflow, the project also provides a containerized Docker setup, a data-management application, and a prompt-focused evaluation tool.

## What The Platform Does

The AI Evaluation Tool ecosystem is designed to help teams test, benchmark, and review conversational AI systems across real-world use cases. It supports:

- automated execution against API, WhatsApp, and web-based targets
- evaluation across safety, quality, language, performance, and privacy dimensions
- LLM-as-judge workflows for nuanced scoring
- structured storage and management of test assets
- report generation for downstream analysis and review

## Main Areas

- [AI Evaluation Tool](./aievaluation_tool.md)
- [Docker Run](./docker_run.md)
- [TDMS](./tdms.md)
- [PQET](./pqet.md)

## How The Pieces Fit Together

The core CLI workflow handles importing data, executing testcases, analyzing responses, and generating reports. Docker provides a reproducible runtime for those services. TDMS helps teams manage the underlying test assets and metadata. PQET focuses specifically on prompt and expected-response quality, making it useful before or alongside broader end-to-end evaluation runs.

## Who This Is For

- AI and ML engineers building or validating conversational systems
- QA teams responsible for structured testing
- product teams reviewing system behavior before release
- teams working with multilingual, safety-sensitive, or compliance-sensitive deployments

## Where To Go Next

- For the command-line workflow, continue to [AI Evaluation Tool CLI](../cli/index.md).
- For containerized execution, continue to [Docker Setup](../docker_setup/index.md).
- For the execution dashboard, continue to [UI](../ui/index.md).
- For data management, continue to [UI](../ui/index.md).
- For prompt-focused evaluation, continue to [PQET](../pqet/index.md).
