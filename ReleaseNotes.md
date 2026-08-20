### **Conversational AI Evaluation Tool - Version 2.0.1**

#### **Description**:

Version 2.0.1 is a stabilization and depth release built on top of the Docker-first foundation shipped in 2.0. It focuses on hardening the TDMS + Dashboard workflow end-to-end (target/credentials management, test run execution, live status, and analysis), upgrading the evaluation strategy engine to use LLM-judge reasoning with richer context, and modernizing the data/model-serving layer with MariaDB and self-hosted Ollama. Alongside these, well over a hundred usability and correctness fixes were made across the Test Data Management System (TDMS) and the Test Case Executor Dashboard based on real usage feedback.

#### **New Features**

- **Test Run Loop & Run Controls**

    Create and Continue Test Run flows were rebuilt around a dedicated `Loop` component, adding proper run-completion handling, a working **Stop Run** button (backed by an `analysis stop` endpoint), and clearer status/duration reporting. The `agentResponse` field is now tracked end-to-end and reasoning text is formatted more legibly in run details.

- **Reworked Analysis Engine & Reporting**

    Analysis execution was refactored into a new mode with clearer state transitions, a stop control, and correct handling of failed evaluations (scores now resolve to `None` on error instead of silently defaulting). Report generation was consolidated into an `EvaluationReport` class for more maintainable PDF/report output, and the run-status WebSocket layer (`ws_manager`) now uses per-connection send locks and automatically drops stale/disconnected clients instead of failing broadcasts.

- **LLM-Judge Reasoning Across Evaluation Strategies**

    `Robustness_OutOfDomain` was refactored to use an LLM judge (`judge_prompt`) with target-domain context instead of heuristic refusal/drift detection, and the shared `get_reason()` helper used across metrics now accepts `user_prompt` and `target_domain`, giving Privacy, Bias, Toxicity, and Fairness/Stereotype checks more context-aware, human-readable explanations. Toxicity scoring was also corrected (removed an inverted/negated `Toxicity_Level` calculation) and tokenizer input handling was streamlined.

- **Target, Credentials & XPath Management Overhaul**

    Targets now support optional credentials, per-field XPath history, and dedicated Credentials/XPath editors, replacing the older combined form. WhatsApp message filtering and XPath handling were refactored for reliability, with added emoji support for robustness testing scenarios.

- **MariaDB + Self-Hosted Ollama Model Serving**

    `docker-compose.yml` now provisions a MariaDB service (replacing the previous local DB fallback) and an Ollama stack — `ollama` (with optional GPU reservation), `ollama-init` (auto-pulls the configured judge model), and `ollama-warmup` (verifies the model responds before the app comes up) — enabling fully self-hosted judge-model inference in production deployments.

- **Expanded Reference Documentation**

    Added a **Conversational AI Metrics and Submetrics Definitions** spreadsheet and an **Evaluation Metrics Reference** PDF, and refreshed the TDMS/Dashboard UI and CLI setup guides to match the current stack.

#### **Improvements & Fixes**

- **TDMS**: fixed delete functionality across Targets/Test Cases/Test Plans/Test Runs; enforced testcase-to-test-plan matching validation; made the "Description" field mandatory on test plans; unified "Name" field labeling across Add/Edit dialogs and list views; fixed pagination double-arrow, table header/data overlap, and user list password-visibility toggle bugs; fixed username validation, logout navigation-blocker, and page-not-found issues on the Users list.
- **Dashboard**: fixed report-download alerts, "Analysis not completed" messaging (replacing a bare `-`), serial numbers replaced with actual record IDs, close-icon/`has_failed_cases` handling, targets/search dropdown mismatches, and general page-load performance.
- **Strategy Engine**: refactored file-path handling in `compute_error_rate`, `compute_mtbf`, and `tat_tpm_mvh`; normalized metric-name casing in safety evaluation; updated the bias-detection model and scoring logic to return a proper bias assessment score.
- **Infrastructure**: added `build-essential`/`gcc` to the backend Dockerfile for native dependency builds; refactored database configuration loading to drop the local-config fallback in favor of environment-driven config; added a configurable `TIME_ZONE` environment variable; added named containers for the Ollama warm-up service.