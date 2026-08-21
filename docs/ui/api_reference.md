# API Reference

This page summarizes the main endpoints used by TDMS and dashboard UI clients.

## Base URLs

- TDMS backend: `http://localhost:7250`
- Dashboard backend: `http://localhost:7000` (from `config.json`)
- Auth service: `http://localhost:7500`
- Dashboard WebSocket: `ws://localhost:7000/ws/test-run`

UI URLs (when served via NGINX):

- TDMS UI: `http://localhost:8080`
- Dashboard UI: `http://localhost:3000`

## Auth Service Endpoints

- `POST /login`
- `POST /refresh`
- `POST /logout`
- `GET /web/login`
- `GET /web/logout`

## TDMS v2 Resource Families

All prefixed by `http://localhost:7250/api/v2`.

- `/testcases`
- `/targets`
- `/domains`
- `/languages`
- `/prompts`
- `/llm-prompts`
- `/responses`
- `/strategies`
- `/metrics`
- `/testplans`

Special utility endpoints:

- `/targets/target/types`
- `/prompts/user-prompt`
- `/prompts/system-prompt`
- `/testplans/metrics/all`

Common TDMS v1 endpoints still used by UI:

- `GET /api/dashboard`
- `GET /api/users/me`
- `GET /api/users`

## Dashboard API Endpoints

Common endpoints on dashboard backend:

- `GET /get_all_filters`
- `GET /get_all_test_runs`
- `POST /start-run`
- `POST /continue-run`
- `POST /continue-run-with-plan`
- `POST /test-runs/{run_id}/stop`
- `GET /test-runs/{run_name}`
- `GET /test-runs/{run_name}/timeline`
- `GET /test-runs/{run_name}/summary`
- `GET /test-runs/{run_name}/evaluation-summary`
- `GET /test-runs/{run_name}/evaluation-report` (Excel `.xlsx`)
- `GET /report/{run_name}` (PDF report used by current UI actions)
- `GET /analyse/{runName}`
- `GET /analyse/{runName}/details`
- `GET /analyse/{runName}/status`
- `POST /analyse/{runName}/stop`
- `GET /conversations/full/{conversation_id}`
- `GET /testcases/{testcase_name}`
- `GET /targets/{target_name}/metadata`
- `GET /__dev/config` (enabled when `DEV_CONFIG_ENABLED` is set)
- `POST /__dev/config`

## Integration Dependency

Dashboard execution depends on interface manager availability:

- Interface manager default URL from root config: `http://localhost:8000`
- Dashboard backend reads this integration configuration from repository root [`config.json`](../../config.json)
