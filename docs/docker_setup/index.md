# Docker Setup

This section documents the current Docker workflow for the AI Evaluation Tool, with a UI-first setup and full CLI support from the same stack.

Use this section when you want to run the platform from scratch with reproducible service orchestration.

## What This Section Covers

- Docker prerequisites and architecture
- from-scratch setup with minimal and advanced configuration
- UI workflow through the nginx entrypoint
- CLI workflow through the `app-backend` runtime container
- GPU endpoint patterns for local and remote inference

## Chapters

- [Setup And Configuration][setup-and-configuration]
- [GPU Setup][gpu-setup]
- [Docker Run CLI][docker-run]
- [Docker Run UI][docker-run-ui]

## Stack Overview

The Docker stack in this repository is built around the services defined in [docker-compose.yml][docker-compose]:

- `db` for MariaDB
- `selenium-browser` for Chromium automation and noVNC viewing
- `interface-manager` for target communication
- `auth-service` for authentication and route handling
- `app-backend` for TCE backend and CLI execution commands
- `tdms-backend` and `tdms-frontend` for TDMS
- `app-front-end` for TCE frontend
- `nginx` as the single public entrypoint

In standard usage, users access both TCE and TDMS through `nginx` on `http://localhost:${NGINX_PORT:-80}`.

## How The Docker Workflow Fits Together

1. Configure `.env` and repository JSON config files.
2. Build images.
3. Start the stack through `nginx` for UI usage.
4. Run importer, execution, analysis, and reporting via `app-backend` for CLI usage.
5. Stop or reset the stack as needed.

## Related Sections

- [Setup And Configuration](./setup_and_configuration.md)
- [GPU Setup](./gpu_setup.md)
- [Docker Run CLI](./docker_run.md)
- [Docker Run UI](./docker_run_ui.md)
- [TDMS + Dashboard UI Overview](../TDMS_and_Dashboard_ui/index.md)
- [Authentication And Roles](../TDMS_and_Dashboard_ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../TDMS_and_Dashboard_ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../TDMS_and_Dashboard_ui/test_runs_manual.md)
- [Run Configuration Manual](../TDMS_and_Dashboard_ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../TDMS_and_Dashboard_ui/analysis_and_run_details_manual.md)
- [Troubleshooting](../TDMS_and_Dashboard_ui/troubleshooting.md)

[docker-compose]: ../../docker-compose.yml
[setup-and-configuration]: ./setup_and_configuration.md
[gpu-setup]: ./gpu_setup.md
[docker-run]: ./docker_run.md
[docker-run-ui]: ./docker_run_ui.md
