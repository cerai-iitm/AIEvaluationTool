# Docker Setup

This section explains how to run the AI Evaluation Tool with Docker: first start, ports and URLs, configuration, the command-line workflow, GPU model services, and running across several machines.

## Quick Start

On a fresh clone, with Docker and Docker Compose installed:

```bash
cp .env.example .env            # then edit the values you need
docker compose up -d
```

Then open [http://localhost:8100/](http://localhost:8100/) and log in with a default account (for example `admin` / `admin123`). The first start can take about 10 minutes while the images download.

- **Port `8100` is the default and can be changed.** If it is taken, set `NGINX_PORT` in `.env`. See [Changing The Port](./docker_run_ui.md#changing-the-port).
- Everything is served through that one port. The other services are internal.

## Chapters

| Page | Use This Page To |
|---|---|
| [Setup And Configuration](./setup_and_configuration.md) | install, fill in `.env`, know every setting and default |
| [Docker Run UI](./docker_run_ui.md) | know the addresses and ports, change the port, understand the login flow, run the development stack |
| [Docker Run CLI](./docker_run.md) | run importer, execution, analysis and reports from a shell in the backend container |
| [GPU Setup](./gpu_setup.md) | choose between the bundled model services and remote GPU endpoints |
| [Multi-Node Stack](./multi_node_stack.md) | deploy across two or more machines with Docker Swarm |
| [Scaling And Capacity](./scaling_and_capacity.md) | set the number of browsers and backend copies for many concurrent users |

## Choosing A Page By Goal

| Goal | Page |
|---|---|
| try the tool on my machine | Quick Start above, then [Docker Run UI](./docker_run_ui.md) |
| change a port or a password | [Setup And Configuration](./setup_and_configuration.md) |
| change frontend or backend code | [Docker Run UI, Development Stack](./docker_run_ui.md#development-stack) |
| run tests without the UI | [Docker Run CLI](./docker_run.md) |
| use my own GPU server | [GPU Setup](./gpu_setup.md) |
| support many people at once | [Multi-Node Stack](./multi_node_stack.md) and [Scaling And Capacity](./scaling_and_capacity.md) |

## Services Overview

The application is a set of containers defined in [docker-compose.yml](../../docker-compose.yml):

- `db` for MariaDB and `redis` for shared job state
- `selenium-hub` and `chrome-node` for the Selenium grid that drives target applications (`chrome-node` is the browser; see `SELENIUM_NODE_COUNT`)
- `interface-manager` for communication with the target applications
- `auth-service` for authentication and role-based redirects
- `app-backend` for the Test Case Execution (TCE) backend and CLI commands
- `tdms-backend` and `tdms-frontend` for the Test Data Management System (TDMS)
- `app-front-end` for the TCE UI
- `nginx` as the single public entrypoint

## Compose Files And Profiles

| File | Purpose |
|---|---|
| `docker-compose.yml` | the main stack. Publishes only `nginx` (and the live-view ports `7900` to `7924`). |
| `docker-compose.dev.yml` | standalone development stack: hot-reload frontends, published backend ports, images built locally. Used on its own, without the main file. |
| `stack-compose.yml` | the same application for a multi-node Docker Swarm. See [Multi-Node Stack](./multi_node_stack.md). |

Profiles for the main file (they add GPU model services):

- `prod`: `ollama`, `ollama-init`, `ollama-warmup` and `sarvam-ai`
- `sarvam`: only `sarvam-ai`

## Workflow Overview

1. Prepare `.env` and the config files.
2. Build and start the stack.
3. Open the UI through `nginx`, or run the CLI inside `app-backend`.
4. Stop or reset the stack when finished.

## Related Documentation

- [UI Overview](../ui/index.md)
- [Authentication And Roles](../ui/authentication_and_roles.md)
- [TDMS Dashboard Manual](../ui/tdms_dashboard_manual.md)
- [Test Runs Manual](../ui/test_runs_manual.md)
- [Run Configuration Manual](../ui/run_configuration_manual.md)
- [Analysis And Run Details Manual](../ui/analysis_and_run_details_manual.md)
- [Troubleshooting](../ui/troubleshooting.md)
