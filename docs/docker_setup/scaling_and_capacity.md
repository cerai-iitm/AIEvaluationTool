# Scaling And Capacity

This page explains what limits how many people can use the tool at the same time, and which settings raise those limits. It applies to the single-host stack and to the [multi-node stack](./multi_node_stack.md).

## Concurrency Limits

| Resource | Limiting Factor | How To Increase It |
|---|---|---|
| Browser sessions | number of `chrome-node` containers | `SELENIUM_NODE_COUNT` |
| Model requests | GPU memory and the model in use | more GPU memory, or more GPUs (see [GPU Setup](./gpu_setup.md)) |
| Backend requests | number of backend containers | scale `app-backend` (see [Scalable Services](#scalable-services)) |
| WhatsApp Web targets | WhatsApp's own linked-device limit | cannot be raised here |

Model capacity depends on your GPU memory, the model you run and the number of parallel requests you allow, so it must be sized for your own hardware. The backend services are light and rarely become the bottleneck.

## Selenium Browser Concurrency

Browser automation runs on a Selenium grid: one `selenium-hub` and several `chrome-node` containers. Each node runs one browser session at a time. Each test run uses one node for its whole duration, and its **View Test Execution** link shows that browser. So the number of nodes is the number of test runs that can execute at the same time.

Set the number of nodes in `.env`:

```env
SELENIUM_NODE_COUNT=10
```

Apply it with `docker compose up -d` (or redeploy the stack).

| Mode | Default | Maximum |
|---|---|---|
| Single host (`docker-compose.yml`) | 2 | 25 (ports `7900` to `7924` are published, one per node) |
| Multi-node (`stack-compose.yml`) | 25 | no fixed limit |

As a guide, use one node for each person who may run a test at the same time, plus a few spare. Each active browser session needs roughly 0.5 to 1 GB of memory.

## Scalable Services

| Service | Multiple Instances Supported | Notes |
|---|---|---|
| `chrome-node` | yes | the main way to scale |
| `app-front-end`, `tdms-frontend` | yes | static files |
| `app-backend` | yes | each login stays on one copy, so session state is consistent |
| `tdms-backend`, `auth-service` | yes on a single host | kept at 1 in the multi-node stack |
| `interface-manager` | no | it keeps the browser session pool in memory |
| `selenium-hub` | no | a second hub would be a separate grid |
| `db`, `redis` | no | not clustered |
| `ollama`, `sarvam-ai` | one per GPU | each copy needs its own GPU memory |

Single host example:

```bash
docker compose up -d --scale app-backend=4
```

Scaling does not work with the [development stack](./docker_run_ui.md#development-stack), because it publishes fixed host ports. On the multi-node stack, see [Operating The Stack](./multi_node_stack.md#operating-the-stack).

## Known Limitations

- WhatsApp Web allows a limited number of linked devices, so the number of simultaneous WhatsApp test runs is limited no matter how many browser nodes exist.
- If a browser session ends and a new one starts during a run, an already open **View Test Execution** tab still points at the old browser. Open the link again.
