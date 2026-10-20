# Setup

Use this guide to run TDMS and the Test Case Execution Tool (Dashboard) locally without Docker. To run everything in Docker instead, see [Docker Setup](../docker_setup/index.md).

## UI And Services

### Frontend UIs

- `TDMS UI` (Vite build output: `dist/`)
- `Test Case Execution Dashboard UI` (CRA build output: `build/`)

### Other User-Facing Web Interface

- `Central Login UI` is served by the auth backend at `/web/login` (no separate frontend build needed)

### Backend Services

- `auth-service` (`localhost:7500`)
- `tdms-backend` (`localhost:7250`)
- `dashboard-backend` (`localhost:7000` from `config.json`)
- `interface-manager` (`localhost:8000`)

## Prerequisites

The system requirements and the MariaDB installation are the same as for the command-line setup. Follow these sections of [Initial Setup And Configuration](../cli/initial_setup_and_configuration.md), then come back here:

- [System Requirements](../cli/initial_setup_and_configuration.md#system-requirements)
- [Install MariaDB](../cli/initial_setup_and_configuration.md#install-mariadb) (skip it if you use SQLite)
- [Install ChromeDriver](../cli/initial_setup_and_configuration.md#install-chromedriver)

## Create Required `.env` Files

Create and populate all required `.env` files before starting services.

### Root `.env` (Repository Root)

This is used by shared runtime components (for example `interface_manager` and API key based providers).

```bash
cp .env.example .env
```

Example values in root `.env`:

```env
OLLAMA_URL=http://localhost:12434
GPU_URL=http://localhost:16000
LLM_AS_JUDGE_MODEL=
PERSPECTIVE_API_KEY=
SARVAM_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=
```

### TDMS Frontend `.env`

Create `src/app/TDMS/front-end/.env`:

```env
VITE_API_BASE_URL="http://localhost:7250"
VITE_AUTH_SERVICE_URL="http://localhost:7500"
VITE_TEST_RUNS_HOME_URL="http://localhost:3000"
```

### Dashboard Frontend `.env`

Create `src/app/TestCaseExecutorDashboard/front-end/.env`:

```env
REACT_APP_API_BASE_URL="http://localhost:7000"
REACT_APP_AUTH_SERVICE_URL="http://localhost:7500"
REACT_APP_TDMS_API_BASE_URL="http://localhost:7250"
REACT_APP_TEST_DATA_URL="http://localhost:8080/dashboard"
REACT_APP_USER_LIST_URL="http://localhost:8080/users"
```

### Auth Service `.env`

Create `src/app/auth_service/.env`:

```env
TCE_APP_URL="http://localhost:3000"
TDMS_APP_URL="http://localhost:8080/dashboard"

```

### Strategy `.env`

For strategy defaults used by `src/lib/strategy/utils_new.py`, keep `src/lib/strategy/.env` present.

```bash
cp src/lib/strategy/.env.example src/lib/strategy/.env
```

Expected values:

```env
DATA_PATH=data/
DEFAULT_VALUES_PATH=data/defaults.json
EXAMPLES_DIR=data/examples/
IMAGES_DIR=data/images/
```

Important:

- Keep all runtime configuration in these `.env` files.
- Do not pass `VITE_*` or `REACT_APP_*` variables inline in run commands.

## Configure Root `config.json`

Update repository root [`config.json`](../../config.json).

For local SQLite:

```json
{
  "db": {
    "engine": "sqlite",
    "file": "AIEvaluationData.db"
  },
  "port": {
    "back-end": "7000",
    "interface-manager": "8000"
  }
}
```

For local MariaDB:

```json
{
  "db": {
    "engine": "mariadb",
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "database": "aievaluationtool"
  },
  "port": {
    "back-end": "7000",
    "interface-manager": "8000"
  }
}
```

Important:

- TDMS backend and Dashboard backend reads `db.engine`.
- Keep both keys aligned.

## Install Dependencies

From repository root:

```bash
pip install -r requirements.txt
```

Install UI dependencies:

```bash
cd src/app/TDMS/front-end && npm install
cd ../../TestCaseExecutorDashboard/front-end && npm install
```

## Run Backend Services Locally

Start each service in a separate terminal.

1. Auth service:

```bash
cd src/app/auth_service
python main.py
```

2. TDMS backend:

```bash
cd src/app/TDMS/back-end
python main.py
```

3. Dashboard backend:

```bash
cd src/app/TestCaseExecutorDashboard
python back-end/main.py
```

4. Interface manager:

```bash
cd src/app/interface_manager
python main.py
```
## GPU Setup

For GPU setup instructions, refer to [GPU setup.](../cli/gpu_setup.md).

## Run Frontend

This is best for development and frequent UI changes.

1. Run TDMS frontend:

```bash
cd src/app/TDMS/front-end
npm run dev
```

2. Run Dashboard frontend:

```bash
cd src/app/TestCaseExecutorDashboard/front-end
npm start
```

Access URLs in this mode:

- TDMS UI: `http://localhost:8080`
- Dashboard UI: `http://localhost:3000`
- Central login UI: `http://localhost:7500/web/login`
## Validation Checklist

- Backend services are reachable on `7500`, `7250`, `7000`, and `8000`.
- TDMS login redirects to auth and returns correctly.
- Dashboard login redirects to auth and returns correctly.
- TDMS `Home` link opens dashboard.
- Dashboard `Test Data` link opens TDMS.
- New run and continue run flows can load filters and start execution.
