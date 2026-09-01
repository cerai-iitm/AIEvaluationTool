# Setup And Configuration

This page explains how to run the AI Evaluation Tool from scratch using Docker, with separate flows for:

- production UI usage through `nginx`
- development usage with exposed service ports
- CLI-based usage through the backend container

It is aligned with the current Compose stack (`app-backend`, `app-front-end`, `auth-service`, `tdms-backend`, `tdms-frontend`, `nginx`) and the development override file (`docker-compose.dev.yml`).

## Prerequisites

- Docker Engine `24+`
- Docker Compose `v2+`
- Repository cloned locally

## Current Docker Stack

Primary services in [docker-compose.yml][docker-compose]:

- `db` (MariaDB)
- `selenium-browser` (Chrome + WebDriver + noVNC)
- `interface-manager` (target interaction service)
- `auth-service` (authentication and route redirects)
- `app-backend` (TCE backend + CLI runtime environment)
- `tdms-backend` (TDMS API)
- `app-front-end` (TCE UI build)
- `tdms-frontend` (TDMS UI build)
- `nginx` (single public entrypoint and reverse proxy)

Public access is through `nginx` on `http://localhost:${NGINX_PORT:-80}`.

## Compose Modes

### Production Mode

Use only `docker-compose.yml` for the production-style local stack.

```bash
docker compose up -d --build nginx
```

This exposes only the nginx entrypoint to the host. Backend, database, Selenium, and frontend services communicate over the internal Docker network.

### Development Mode

Use both Compose files when developing or debugging services directly:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

The development override bind-mounts the repository into service containers and exposes direct ports for the individual services.

Development URLs:

- TCE frontend dev server: `http://localhost:3000`
- TDMS frontend dev server: `http://localhost:8080`
- Dashboard backend API docs: `http://localhost:7000/docs`
- TDMS backend: `http://localhost:7250`
- Auth service docs: `http://localhost:7500/docs`
- Interface Manager docs: `http://localhost:8000/docs`
- Selenium live browser: `http://localhost:7900`

In development mode, use the direct frontend ports above as the primary UI entrypoints. The production nginx route uses `docker/nginx/nginx.conf`; use a development nginx config only if you explicitly wire it into Compose.

### Compose Profiles

The Docker stack also includes optional model-serving profiles:

- `prod`: enables Compose-managed Ollama services (`ollama`, `ollama-init`, `ollama-warmup`) and `sarvam-ai`.
- `sarvam`: enables only the Compose-managed Sarvam AI service.

Use `prod` when you want the Docker stack to include the bundled model-serving services:

```bash
docker compose --profile prod up -d --build
```

Use `sarvam` when Ollama is hosted elsewhere but Sarvam AI should run through Compose:

```bash
docker compose --profile sarvam up -d sarvam-ai
```

## Configuration Files To Prepare

### 1. Root and Strategy `.env`

Create `.env` if not present:

```bash
cp .env.example .env
```

Minimal runtime values:

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
HF_TOKEN=""
PERSPECTIVE_API_KEY=""
SARVAM_API_KEY=""
GEMINI_API_KEY=""
OPENAI_API_KEY=""
```


### 2. Optional `.env` Overrides (All Compose-Tunable Variables)

Use these only when you need custom ports, DB credentials, or custom frontend/backend routes:

```env
# Public port for nginx
NGINX_PORT=80

# MariaDB
MARIADB_ROOT_PASSWORD=root_password
MARIADB_DATABASE=aievaluationtool
MARIADB_USER=aiet_user
MARIADB_PASSWORD=aiet_password

# Service-level DB fallback values
DB_HOST=db
DB_PORT=3306

# Auth redirects / route integration
TCE_APP_URL=/
TDMS_APP_URL=/tdms/dashboard
AUTH_SERVICE_URL=http://auth-service:7500

# TCE frontend build args
REACT_APP_API_BASE_URL=/api
REACT_APP_AUTH_SERVICE_URL=/auth
REACT_APP_TDMS_API_BASE_URL=/tdms-api
REACT_APP_TEST_DATA_URL=/tdms/dashboard
REACT_APP_USER_LIST_URL=/tdms/users

# TDMS frontend build args
VITE_API_BASE_URL=/tdms-api
VITE_AUTH_SERVICE_URL=/auth
VITE_TEST_RUNS_HOME_URL=/
```

### 3. Root `config.json` (Required For CLI Flow)

Keep Docker-aware values:

- `db.host` should be `db`
- `interface_manager.docker` should be `true`
- `interface_manager.base_url` should be `http://interface-manager:8000`


## Section 1: Run Production UI (Recommended For Most Users)

### Step 1: Start Production UI Stack

```bash
docker compose up -d --build nginx
```

Bringing up `nginx` starts required dependencies (`app-front-end`, `tdms-frontend`, `app-backend`, `tdms-backend`, `auth-service`, `interface-manager`, `db`, `selenium-browser`).

### Step 2: Verify Containers

```bash
docker compose ps
```

### Step 3: Open The Application

- Main UI (TCE): `http://localhost:${NGINX_PORT:-80}/`
- TDMS UI: `http://localhost:${NGINX_PORT:-80}/tdms/`
- Selenium live view (via nginx): `http://localhost:${NGINX_PORT:-80}/selenium/`
- Stack health check: `http://localhost:${NGINX_PORT:-80}/healthz`

For detailed UI workflows after startup, refer to:

- [UI Overview](../ui/index.md)
- [Authentication And Roles](../ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../ui/test_runs_manual.md)
- [Run Configuration Manual](../ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../ui/analysis_and_run_details_manual.md)

## Section 2: Run Development Stack

Use this mode when you need live frontend development servers, direct backend ports, or easier debugging.

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

Open:

- TCE frontend: `http://localhost:3000`
- TDMS frontend: `http://localhost:8080`
- Selenium live browser: `http://localhost:7900`

Stop development stack:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## Section 3: Run Through CLI (Importer, Execution, Analysis, Report)

Use `app-backend` as the CLI runtime container.

### Step 1: Ensure Core Services Are Running

```bash
docker compose up -d db selenium-browser interface-manager auth-service tdms-backend app-backend
```

### Step 2: Import Test Data

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/importer/main.py --config config.json
```

### Step 3: Inspect Plans/Metrics (Optional but Recommended)

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/testcase_executor/main.py --config config.json --get-plans
```

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/testcase_executor/main.py --config config.json --get-metrics
```

### Step 4: Execute Testcases

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/testcase_executor/main.py --config config.json --testplan-id <id> --execute
```

### Step 5: Analyze Responses

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/response_analyzer/analyze.py --config config.json --run-name <run_name>
```

### Step 6: Generate Report

```bash
docker compose run --rm --no-deps -w /app app-backend \
python src/app/response_analyzer/report.py --config config.json --run-name <run_name> --get-report
```

## Optional: Use Built-In Model Services

### Full Production Model Profile

Use the `prod` profile to start the production stack with Compose-managed Ollama and Sarvam AI:

```bash
docker compose --profile prod up -d --build
```

When using this mode, set model URLs to the Compose service names:

```env
OLLAMA_URL="http://ollama:11434/"
GPU_URL="http://sarvam-ai:16000/"
```

### Sarvam AI Only

If you want Compose-managed Sarvam instead of an external `GPU_URL` endpoint:

```bash
docker compose --profile sarvam up -d sarvam-ai
```

Then set:

```env
GPU_URL="http://sarvam-ai:16000/"
```

## Shutdown And Reset

Stop all containers:

```bash
docker compose down
```

Stop and remove volumes (full reset):

```bash
docker compose down -v
```

## Final Pre-Run Checklist

- `.env` created and validated
- Docker service names used in `config.json`
- remote Selenium enabled in `src/app/interface_manager/config.json`
- test data files present under `data/`
- target application details configured correctly

[docker-compose]: ../../docker-compose.yml
