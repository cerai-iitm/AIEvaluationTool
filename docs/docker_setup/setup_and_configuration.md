# Setup And Configuration

This page takes you from a fresh clone to a running application in Docker, and lists every setting you can change.

- Want to just use the UI? Follow the [Quick Start](#quick-start).
- Want to run importer, execution, analysis and reports from the command line? See [Docker Run CLI](./docker_run.md).
- Running on more than one machine? See [Multi-Node Stack](./multi_node_stack.md).

## Prerequisites

- Docker Engine `24+`
- Docker Compose `v2+`
- The repository cloned locally
- Port `8100` free on your machine (or a different port, see [Changing The Port](./docker_run_ui.md#changing-the-port))
- An NVIDIA GPU and `nvidia-container-toolkit` **only** if you run the bundled model services (`--profile prod`). See [GPU Setup](./gpu_setup.md).

## Quick Start

1. **Create `.env`:**

   ```bash
   cp .env.example .env
   ```

2. **Fill in the values you need** (see [Environment File (`.env`)](#environment-file-env)). The model endpoints and API keys depend on which metrics you run.

3. **Start the application:**

   ```bash
   docker compose up -d
   ```

   The first start can take about 10 minutes while the images download. This starts every service, including the database, Redis and the Selenium grid with its browser nodes. (Do not start only `nginx`: that skips the browser nodes, so web-target runs would have no browser.)

4. **Check it is healthy:**

   ```bash
   docker compose ps
   ```

5. **Open the application** at [http://localhost:8100/](http://localhost:8100/) and log in. A default account is `admin` / `admin123`; change it after the first login. Details: [Authentication And Roles](../ui/authentication_and_roles.md).

Next: [Docker Run UI](./docker_run_ui.md) explains the addresses, ports and screens.

## Services In The Stack

Services in [docker-compose.yml](../../docker-compose.yml):

| Service | Purpose | Started By Default |
|---|---|---|
| `db` | MariaDB database | yes |
| `redis` | shared job and WebSocket state | yes |
| `selenium-hub` | Selenium grid hub | yes |
| `chrome-node` | browser nodes (`SELENIUM_NODE_COUNT`, default 2) | yes |
| `interface-manager` | talks to the target application through the browser | yes |
| `auth-service` | login, tokens, role-based redirects | yes |
| `app-backend` | TCE backend; also the container for CLI commands | yes |
| `tdms-backend` | TDMS API | yes |
| `app-front-end` | TCE UI | yes |
| `tdms-frontend` | TDMS UI | yes |
| `nginx` | the single public entrypoint and reverse proxy | yes |
| `ollama`, `ollama-init`, `ollama-warmup` | local LLM judge model (needs an NVIDIA GPU) | only with `--profile prod` |
| `sarvam-ai` | Sarvam AI model service (needs an NVIDIA GPU) | with `--profile prod` or `--profile sarvam` |

Only `nginx` (and the browser live-view ports `7900` to `7924`) is published on your machine. Everything else talks over the internal Docker network. For the full ports table, see [Docker Run UI](./docker_run_ui.md#ports).

## Environment File (`.env`)

Docker Compose reads `.env` in the repository root. It is not committed to git, so each machine has its own.

### Required Settings

Example values; set them for your own servers and keys. `.env.example` leaves the model URLs empty.

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
HF_TOKEN=""
PERSPECTIVE_API_KEY=""
SARVAM_API_KEY=""
GEMINI_API_KEY=""
OPENAI_API_KEY=""
TIME_ZONE="Asia/Kolkata"
```

| Variable | Meaning |
|---|---|
| `OLLAMA_URL` | Ollama server used as the judge model. `host.docker.internal` means "the machine running Docker". |
| `GPU_URL` | Sarvam AI service endpoint |
| `LLM_AS_JUDGE_MODEL` | model name used for judging |
| `HF_TOKEN` | Hugging Face token (for downloading models) |
| `PERSPECTIVE_API_KEY`, `SARVAM_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY` | keys for the integrations you use; leave empty for ones you do not |
| `TIME_ZONE` | time zone for timestamps |

### Optional Settings

Everything below has a default. Set a variable in `.env` only to change it.

| Variable | Default | Description | To Apply A Change |
|---|---|---|---|
| `NGINX_PORT` | `8100` | public port | `docker compose up -d` |
| `SELENIUM_NODE_COUNT` | `2` | number of browser nodes (max `25` on one machine) | `docker compose up -d` |
| `OLLAMA_MODEL` | `qwen3:32b` | model pulled by the bundled Ollama (`--profile prod`) | `docker compose --profile prod up -d` |
| `MARIADB_ROOT_PASSWORD` | `root_password` | database | see note below |
| `MARIADB_DATABASE` | `aievaluationtool` | database | see note below |
| `MARIADB_USER` | `aiet_user` | database | see note below |
| `MARIADB_PASSWORD` | `aiet_password` | database | see note below |
| `DB_HOST` | `db` | where services find the database | `docker compose up -d` |
| `DB_PORT` | `3306` | where services find the database | `docker compose up -d` |
| `TCE_APP_URL` | `/` | where `admin` and `manager` land after login | `docker compose up -d` |
| `TDMS_APP_URL` | `/tdms/dashboard` | where `curator` and `viewer` land after login | `docker compose up -d` |
| `AUTH_SERVICE_URL` | `http://auth-service:7500` | how `tdms-backend` reaches the auth service | `docker compose up -d` |

**Database credentials:** MariaDB only reads these on its very first start, when it creates the data volume. Changing them later does nothing until you delete the volume (`docker compose down -v`, which erases all data). The defaults are placeholders: change them before putting real data in, and set them **before** the first start.

**Frontend build settings:** these are baked into the frontend images when they are built, so changing one has no effect on the published images. To apply a change, build the frontends yourself with `docker compose build app-front-end tdms-frontend`, then run `docker compose up -d`. The defaults are already correct for the standard setup; change them only if you serve the app under different paths.

| Variable | Default |
|---|---|
| `REACT_APP_API_BASE_URL` | `/api` |
| `REACT_APP_AUTH_SERVICE_URL` | `/auth` |
| `REACT_APP_TDMS_API_BASE_URL` | `/tdms-api` |
| `REACT_APP_TEST_DATA_URL` | `/tdms/dashboard` |
| `REACT_APP_USER_LIST_URL` | `/tdms/users` |
| `VITE_API_BASE_URL` | `/tdms-api` |
| `VITE_AUTH_SERVICE_URL` | `/auth` |
| `VITE_TEST_RUNS_HOME_URL` | `/` |

## Configuration Files

| File | Used for | What to check |
|---|---|---|
| `config.json` (repository root) | the CLI flow and `app-backend` | `db.host` is `db`; `interface_manager.docker` is `true`; `interface_manager.base_url` is `http://interface-manager:8000` |
| `src/app/interface_manager/config.json` | browser automation | `selenium_mode` is `"remote"` and `selenium_remote_url` is `"http://selenium-hub:4444/wd/hub"` |
| `src/app/interface_manager/xpaths.json` | element selectors for web and WhatsApp targets | stable relative XPaths for login fields, prompt box, response area, logout |
| `src/app/interface_manager/credentials.json` | logins for the target web applications | add or update the entry for each target you test |
| `data/` | test data files for the importer | the files you want to import are present |

`xpaths.json` and `credentials.json` are mounted into the containers, so edit them on your machine and restart `interface-manager` (`docker compose restart interface-manager`). They are not read from the image.

## Compose Profiles

Profiles switch on optional model-serving containers. They are not started by default and need an NVIDIA GPU.

| Profile | Adds | Use it when |
|---|---|---|
| `prod` | `ollama`, `ollama-init`, `ollama-warmup` and `sarvam-ai` | you want the whole application together with the bundled models |
| `sarvam` | only `sarvam-ai` | Ollama is hosted elsewhere but Sarvam AI should run in Docker |

With no profile, the application expects both model servers to be reachable at the addresses in `.env`.

Set the model URLs in `.env` to match how you run the models:

| Setup | `OLLAMA_URL` | `GPU_URL` |
|---|---|---|
| `prod` profile | `http://ollama:11434/` | `http://sarvam-ai:16000/` |
| `sarvam` profile | your own Ollama server | `http://sarvam-ai:16000/` |
| No profile | your own Ollama server | your own Sarvam AI server |

For how to start the application with a profile, see [Start With Model Services](./docker_run_ui.md#start-with-model-services-profiles). For remote GPU servers and other options, see [GPU Setup](./gpu_setup.md).

## Pre-Run Checklist

- `.env` created, with the model URLs and keys you need
- port `8100` free, or `NGINX_PORT` set to a free one
- database passwords changed from the defaults (before the first start)
- `config.json` uses the Docker service names (`db`, `interface-manager`)
- remote Selenium enabled in `src/app/interface_manager/config.json`
- `xpaths.json` and `credentials.json` match the targets you will test
- test data files are present under `data/`

## Running And Next Steps

- Start, stop and reset the application: [Docker Run UI](./docker_run_ui.md)
- Command-line workflow (import, execute, analyze, report): [Docker Run CLI](./docker_run.md)
- Hot-reload development with separate ports: [Docker Run UI, Development Stack](./docker_run_ui.md#development-stack)
- Several machines, many users: [Multi-Node Stack](./multi_node_stack.md)
