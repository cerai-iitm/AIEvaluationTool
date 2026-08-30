# Docker Setup

This section documents the current Docker workflow for the AI Evaluation Tool, with a UI-first production stack, a separate Docker development stack, and full CLI support from the backend runtime container.

Use this section when you want to run the platform from scratch with reproducible service orchestration.

## What This Section Covers

- Docker prerequisites and architecture
- from-scratch production setup with `docker-compose.yml`
- development setup with `docker-compose.dev.yml`
- UI workflow through the nginx entrypoint
- CLI workflow through the `app-backend` runtime container
- Compose profiles for production model services
- GPU endpoint patterns for local and remote inference

## Chapters

- [Setup And Configuration][setup-and-configuration]
- [GPU Setup][gpu-setup]
- [Docker Run CLI][docker-run]
- [Docker Run UI][docker-run-ui]

## Stack Overview

The production Docker stack is built around the services defined in [docker-compose.yml][docker-compose]:

- `db` for MariaDB
- `selenium-browser` for Chromium automation and noVNC viewing
- `interface-manager` for target communication
- `auth-service` for authentication and route handling
- `app-backend` for TCE backend and CLI execution commands
- `tdms-backend` and `tdms-frontend` for TDMS
- `app-front-end` for TCE frontend
- `nginx` as the single public entrypoint

In standard usage, users access both TCE and TDMS through `nginx` on `http://localhost:${NGINX_PORT:-80}`.

## Compose Files And Profiles

- `docker-compose.yml` is the production-oriented stack. It exposes only `nginx` to the host and keeps service ports internal.
- `docker-compose.dev.yml` is the development override. It bind-mounts source code and exposes service ports such as `3000`, `7000`, `7250`, `7500`, `8000`, `8080`, and `7900`.
- `prod` profile enables the Compose-managed Ollama services (`ollama`, `ollama-init`, `ollama-warmup`) and `sarvam-ai`.
- `sarvam` profile enables only the Compose-managed Sarvam AI service.

## How The Docker Workflow Fits Together

1. Configure `.env` and repository JSON config files.
2. Choose production or development Compose mode.
3. Build and start the stack.
4. Open the UI through `nginx` in production, or direct frontend ports in development.
5. Run importer, execution, analysis, and reporting via `app-backend` for CLI usage.
6. Stop or reset the stack as needed.

## Related Sections

- [Setup And Configuration](./setup_and_configuration.md)
- [GPU Setup](./gpu_setup.md)
- [Docker Run CLI](./docker_run.md)
- [Docker Run UI](./docker_run_ui.md)
- [UI Overview](../ui/index.md)
- [Authentication And Roles](../ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../ui/test_runs_manual.md)
- [Run Configuration Manual](../ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../ui/analysis_and_run_details_manual.md)
- [Troubleshooting](../ui/troubleshooting.md)

[docker-compose]: ../../docker-compose.yml
[setup-and-configuration]: ./setup_and_configuration.md
[gpu-setup]: ./gpu_setup.md
[docker-run]: ./docker_run.md
[docker-run-ui]: ./docker_run_ui.md
