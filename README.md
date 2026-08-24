# Conversational AI Evaluation Tool - v2.0.1

## 1. Overview

AIEvaluationTool is an end-to-end platform for evaluating conversational AI systems across API, web, and WhatsApp-style interfaces.

It combines:

- **TDMS** for managing test data (test cases, plans, prompts, strategies)
- **Test Case Execution Dashboard** for running evaluations, tracking runs, and reviewing results
- **CLI workflow** for importer, execution, analysis, and report generation

For full details, refer to the [official documentation](https://cerai-iitm.github.io/AIEvaluationTool/).

## 2. Architecture And Design

TDMS and the Dashboard run as a unified application layer behind a single Docker gateway.

![System Architecture](screenshots/Arch.jpg)

## 3. Configuration

Docker reads runtime values from `.env` and application-level configuration from `config.json`.

### 3.1 Create Environment File

```bash
cp .env.example .env
```

### 3.2 Required Files

- Root `.env`
- Root `config.json`
- `src/app/interface_manager/config.json` (for browser automation settings)

### 3.3 XPath Configuration For Web App Automation

For web/WhatsApp targets, configure element selectors in:

- `src/app/interface_manager/xpaths.json`
- `src/app/interface_manager/credentials.json`

Use stable relative XPath values for login fields, prompt input areas, response containers, and logout elements.

Detailed configuration guide: [Docker Setup and Configuration](docs/docker_setup/setup_and_configuration.md)

## 4. Getting Started With Docker

### 4.1 Build And Start

```bash
docker compose up -d --build nginx
```

For the Docker development stack, use:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### 4.2 Open The Application

- TCE UI: `http://localhost:${NGINX_PORT:-80}/`
- TDMS UI: `http://localhost:${NGINX_PORT:-80}/tdms/`
- Selenium live view: `http://localhost:${NGINX_PORT:-80}/selenium/`
- Health: `http://localhost:${NGINX_PORT:-80}/healthz`

### 4.3 Stop Or Reset

```bash
docker compose down
# full reset
docker compose down -v
```

### 4.4 Other Run Modes

- Docker CLI flow: [Docker Run CLI](docs/docker_setup/docker_run.md)
- Docker UI flow: [Docker Run UI](docs/docker_setup/docker_run_ui.md)
- GPU model setup: [Docker GPU Setup](docs/docker_setup/gpu_setup.md)
- Non-Docker/local setup: [UI Setup](docs/ui/setup.md)
- Full docs portal: [AIEvaluationTool Documentation](https://cerai-iitm.github.io/AIEvaluationTool/)

## 5. How The Project Came To Life

![AI Eval Tool Evolution](screenshots/AIEvalTool.gif)

Made with [Gource](https://gource.io/)
