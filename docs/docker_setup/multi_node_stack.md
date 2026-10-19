# Multi-Node Stack

This page explains how to run the AI Evaluation Tool across **two or more machines** as a single Docker Swarm deployment, and how to size it for many concurrent users.

If you only need to run the tool on one machine, you do not need this page. Use [Setup And Configuration](./setup_and_configuration.md) instead.

## Single Host Compared With Multi-Node

| | Single host (`docker-compose.yml`) | Multi-node (`stack-compose.yml`) |
|---|---|---|
| Command | `docker compose up` | `docker stack deploy` |
| Machines | 1 | 2 or more, joined in a Swarm |
| Builds images | yes (`build:`) | no, it only pulls images from a registry |
| Selenium browsers | 2 by default (`SELENIUM_NODE_COUNT`) | 25 by default, spread across nodes |
| GPU services | optional (`--profile prod`) | always included |
| Typical use | development, demo, small team | many concurrent users, more browsers and GPUs |

## Service Placement

`stack-compose.yml` defines the same application as `docker-compose.yml`. Services that own state (database, bind-mounted config files) are pinned to one machine labelled `primary`. The stateless ones are free to spread onto the other machine.

| Service | Replicas (Default) | Placement | Reason |
|---|---|---|---|
| `db` | 1 | `primary` | owns the `mariadb_data` volume; MariaDB is not clustered |
| `redis` | 1 | `primary` | shared job and WebSocket state |
| `selenium-hub` | 1 | any | must stay 1: it keeps session bookkeeping in memory |
| `chrome-node` | 25 (`SELENIUM_NODE_COUNT`) | any | stateless; this is what uses the second machine |
| `interface-manager` | 1 | `primary` | must stay 1: it pools Selenium sessions in process |
| `auth-service` | 1 | `primary` | bind-mounts `./data` |
| `app-backend` | 2 (`APP_BACKEND_REPLICAS`) | `primary` | bind-mounts config files |
| `tdms-backend` | 1 | `primary` | bind-mounts `./data` and config files |
| `ollama` | 2 | any | one per GPU node |
| `ollama-init` | 2 (one-shot) | any | pulls the model (`OLLAMA_MODEL`) on each node |
| `sarvam-ai` | 2 | any | one per GPU node |
| `app-front-end` | 1 | any | static build, stateless |
| `tdms-frontend` | 1 | any | static build, stateless |
| `nginx` | 1 | `primary` | bind-mounts `nginx.conf` |

The defaults above come from [stack-compose.yml](../../stack-compose.yml). If you edit that file, trust the file over this table.

## Why A Separate `stack-compose.yml`

`docker stack deploy` understands only part of the Compose format, so the root `docker-compose.yml` cannot be deployed to a Swarm as it is. The differences:

| `docker-compose.yml` | `stack-compose.yml` | Reason |
|---|---|---|
| `build:` | `image:` only | Swarm never builds; it pulls. Images are built and pushed first. |
| `profiles:` | removed | Swarm has no `--profile`; the stack always includes the model services. |
| `env_file: .env` | explicit `environment:` block | `env_file` is not supported by `docker stack deploy`. |
| `restart:` / `container_name:` | `deploy.restart_policy` | Swarm ignores both. |
| `depends_on` conditions | plain lists | Swarm does not wait for health. Services retry their own connections, so a few early errors in logs on a cold start are normal. |
| `chrome-node` ports `7900-7924` | none | Swarm cannot give each replica its own host port. nginx reaches each node's live view over the private overlay network instead (`/vnc-proxy/`). |
| bind mounts, named volumes | `deploy.placement` on `primary` | A relative path or volume exists only on one machine, so the service must run there. |

## Images And The Registry

Both compose files name images `${REGISTRY}/aiet-<name>:${TAG}`:

| Image | Used by |
|---|---|
| `aiet-backend` | `interface-manager`, `auth-service`, `app-backend`, `tdms-backend`, `sarvam-ai` (one shared image; the `command` and `working_dir` of each service choose what runs) |
| `aiet-app-frontend` | `app-front-end` |
| `aiet-tdms-frontend` | `tdms-frontend` |

| Variable | Default | Meaning |
|---|---|---|
| `REGISTRY` | `h1manshuj` | Docker Hub namespace, or `host:port` of a private registry |
| `TAG` | `latest` | Image tag |

The default `REGISTRY` is a temporary placeholder and will move to the project's own namespace. To use a different one, set `REGISTRY` in `.env`. Nothing else needs to change.

## Accessing The Application

Swarm's routing mesh opens the nginx port on **every** node, so the application is reachable at the address of **either** machine:

- [http://localhost:8100/](http://localhost:8100/) on a node itself, or `http://<node-ip>:8100/` from another computer
- If port 8100 is taken, set `NGINX_PORT` in `.env` before deploying. See [Changing The Port](./docker_run_ui.md#changing-the-port).

## Prerequisites

- Two or more machines on the same private network (or VPC), each with Docker Engine 24+.
- An NVIDIA driver and `nvidia-container-toolkit` on every machine whose GPU you want to use. See [GPU Setup](./gpu_setup.md).
- Ports **2377/tcp**, **7946/tcp+udp** and **4789/udp** open between the machines (and only between them).
- A registry that all machines can pull from.

Continue with [Swarm Deployment](#swarm-deployment).

## Swarm Deployment

This page takes two machines from nothing to a running multi-node stack. Read the sections above first for what is deployed and why.

Terms used below:

- **Manager** (`IP1`): the machine that runs the database, config-bound services and GPU services. It is labelled `primary`.
- **Worker** (`IP2`): the second machine. It receives whatever Swarm schedules onto it, mainly `chrome-node` browsers.

### Steps By Machine

| Step | Run On |
|---|---|
| 1. Open firewall ports | both |
| 2. Create the swarm | manager |
| 3. Join the worker | worker |
| 4. Verify the cluster | manager |
| 5. Label the manager | manager |
| 6. Set `nvidia` as default runtime | manager (and any GPU worker) |
| 7. Set up a registry | registry on manager; trust it on both |
| 8. Build and push images | manager |
| 9. Prepare `.env` and config files | manager |
| 10. Deploy | manager |
| 11. Verify the deployment | manager |

The worker never runs `docker stack` or `docker service` commands. Everything after joining is run from the manager.

### 1. Open Firewall Ports

Allow these between the two machines only, never from the public internet:

| Port | Protocol | Purpose |
|---|---|---|
| 2377 | TCP | cluster management (the manager listens) |
| 7946 | TCP and UDP | node discovery and health |
| 4789 | UDP | overlay network: all container-to-container traffic |

On **each** machine, with `<OTHER-IP>` set to the **other** machine's private IP (Ubuntu/Debian with `ufw`):

```bash
sudo ufw allow from <OTHER-IP> to any port 2377 proto tcp
sudo ufw allow from <OTHER-IP> to any port 7946 proto tcp
sudo ufw allow from <OTHER-IP> to any port 7946 proto udp
sudo ufw allow from <OTHER-IP> to any port 4789 proto udp
sudo ufw reload
```

Using `firewalld` or raw `iptables` instead? Allow the same four port/protocol pairs from `<OTHER-IP>`.

**On cloud VMs** (AWS, GCP, Azure), the provider's security group sits in front of the OS firewall. Allow the same ports between the two instances there too, in both directions.

Quick check from each machine. This confirms the TCP ports only; UDP is proven by step 4:

```bash
nc -zv <OTHER-IP> 2377
nc -zv <OTHER-IP> 7946
```

### 2. Create The Swarm (Manager)

```bash
docker swarm init --advertise-addr <MANAGER-PRIVATE-IP>
```

Copy the `docker swarm join --token ...` command it prints.

### 3. Join The Worker (Worker)

```bash
docker swarm join --token <TOKEN> <MANAGER-PRIVATE-IP>:2377
```

### 4. Verify The Cluster (Manager)

```bash
docker node ls
```

Both nodes must show `Ready` and `Active`. If the worker shows `Down`, recheck step 1, especially UDP 4789 and 7946.

### 5. Label The Manager (Manager)

`stack-compose.yml` pins stateful services to the node labelled `primary`:

```bash
docker node update --label-add primary=true <manager-hostname>
```

### 6. Make `nvidia` The Default Runtime (GPU Machines)

Swarm does not honour the Compose GPU reservation reliably, so GPU access relies on the node's default Docker runtime. In `/etc/docker/daemon.json`:

```json
{
  "default-runtime": "nvidia",
  "runtimes": { "nvidia": { "path": "nvidia-container-runtime", "runtimeArgs": [] } }
}
```

```bash
sudo systemctl restart docker
```

Do this on every machine that has a GPU you want `ollama` and `sarvam-ai` to use. Install the driver and toolkit first: [GPU Setup](./gpu_setup.md).

### 7. Set Up A Registry

Every node must be able to pull the three images. Choose **one** option.

#### Option A: Private Registry (No Account Needed)

On the manager:

```bash
docker run -d -p 5000:5000 --restart unless-stopped --name registry registry:2
```

On **both** machines, add to `/etc/docker/daemon.json`, then restart Docker:

```json
{ "insecure-registries": ["<manager-private-ip>:5000"] }
```

```bash
sudo systemctl restart docker
```

Then set `REGISTRY=<manager-private-ip>:5000` in `.env`.

#### Option B: Docker Hub Or Another Public Registry

Run `docker login` on the manager. Nothing else is needed on either machine. Set `REGISTRY=<dockerhub-username>` in `.env`.

If the repository is **private**, the worker must also be able to pull it. Either run `docker login` on the worker too, or deploy with `--with-registry-auth` in step 10.

### 8. Build And Push Images (Manager)

From the repository root. `REGISTRY` and `TAG` are the same values you will put in `.env`:

```bash
export REGISTRY=<registry-or-dockerhub-username>
export TAG=latest

docker build -f Dockerfile.app-backend --target runtime-base \
  -t $REGISTRY/aiet-backend:$TAG .

docker build -f Dockerfile.app-front-end \
  --build-arg REACT_APP_API_BASE_URL=/api \
  --build-arg REACT_APP_AUTH_SERVICE_URL=/auth \
  --build-arg REACT_APP_TDMS_API_BASE_URL=/tdms-api \
  --build-arg REACT_APP_TEST_DATA_URL=/tdms/dashboard \
  --build-arg REACT_APP_USER_LIST_URL=/tdms/users \
  -t $REGISTRY/aiet-app-frontend:$TAG .

docker build -f Dockerfile.tdms-frontend \
  --build-arg VITE_API_BASE_URL=/tdms-api \
  --build-arg VITE_AUTH_SERVICE_URL=/auth \
  --build-arg VITE_TEST_RUNS_HOME_URL=/ \
  -t $REGISTRY/aiet-tdms-frontend:$TAG .

for img in backend app-frontend tdms-frontend; do
  docker push $REGISTRY/aiet-$img:$TAG
done
```

The `--build-arg` values shown are the defaults. They are baked into the frontend images, so changing them means rebuilding and pushing again.

Repeat this step, then step 10, whenever application code changes.

### 9. Prepare `.env` And Config Files (Manager)

```bash
cp .env.example .env
```

Fill in the keys (`HF_TOKEN`, `SARVAM_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `PERSPECTIVE_API_KEY`, `LLM_AS_JUDGE_MODEL`, `TIME_ZONE`). Set `OLLAMA_URL` and `GPU_URL` to the Swarm service names:

```env
OLLAMA_URL="http://ollama:11434/"
GPU_URL="http://sarvam-ai:16000/"
```

Optional overrides:

| Variable | Default | Meaning |
|---|---|---|
| `REGISTRY` | `h1manshuj` | where images are pulled from (must match step 8) |
| `TAG` | `latest` | image tag (must match step 8) |
| `NGINX_PORT` | `8100` | public port on every node |
| `SELENIUM_NODE_COUNT` | `25` | number of browser nodes |
| `APP_BACKEND_REPLICAS` | `2` | number of `app-backend` copies |
| `OLLAMA_MODEL` | `qwen3:32b` | model pulled by `ollama-init` |

Also confirm these exist in the manager's checkout, because services bind-mount them:

- `config.json`
- `src/app/interface_manager/xpaths.json`
- `src/app/interface_manager/credentials.json`
- `data/`

Those files exist **only on the manager**. That is why every service that mounts them is pinned to the `primary` node. If you remove the pin, copy the files to the other node at the same paths, otherwise the service starts with an empty mount and fails quietly.

### 10. Deploy (Manager)

`docker stack deploy` does not read `.env` by itself, so load it into the shell first:

```bash
set -a
source .env
set +a
docker stack deploy -c stack-compose.yml aiet
```

For a private Docker Hub repository where the worker is not logged in, add `--with-registry-auth`:

```bash
docker stack deploy --with-registry-auth -c stack-compose.yml aiet
```

### 11. Verify The Deployment (Manager)

```bash
docker stack services aiet
docker stack ps aiet
curl -f http://localhost:${NGINX_PORT:-8100}/healthz
```

Every service should reach its desired replica count (for example `25/25` for `chrome-node`). The first start is slow because each GPU node pulls the model. Then open [http://localhost:8100/](http://localhost:8100/), or the manager's or worker's IP on the same port.

### Operating The Stack

The stack is named `aiet`, so services are addressed as `aiet_<service>`. Run all of these on the manager.

| Task | Command |
|---|---|
| Status of all services | `docker stack services aiet` |
| Where each task runs, and errors | `docker stack ps aiet --no-trunc` |
| Follow logs | `docker service logs -f --tail 100 aiet_app-backend` |
| Scale (temporary; reverts on next deploy) | `docker service scale aiet_chrome-node=40` |
| Scale (permanent) | set `SELENIUM_NODE_COUNT` or `APP_BACKEND_REPLICAS` in `.env`, then repeat step 10 |
| Pause one service | `docker service scale aiet_chrome-node=0` |
| Restart a service (rolling) | `docker service update --force aiet_app-backend` |
| Roll back a bad update | `docker service rollback aiet_app-backend` |
| Ship a new image | rebuild and push (step 8), then `docker service update --image $REGISTRY/aiet-backend:$TAG aiet_app-backend` |
| Stop everything | `docker stack rm aiet` |

Notes:

- `docker stack rm` keeps named volumes (database, models). To really wipe data, delete the volume yourself with `docker volume rm` on the node that holds it.
- Swarm has no "restart this one task". Restart the service, or restart the container directly on the node that runs it.
- Only scale services that are safe to run more than once. See [Scaling And Capacity](./scaling_and_capacity.md#scalable-services).

### Troubleshooting

| Symptom | Likely Cause And Fix |
|---|---|
| Worker shows `Down` in `docker node ls` | UDP 4789 or 7946 blocked, here or in the cloud security group. Recheck step 1. |
| Task stuck `Pending` | No node matches the placement. Check the `primary` label (step 5) and `docker stack ps aiet --no-trunc`. |
| `No such image` or pull errors on the worker | The worker cannot reach the registry. Recheck step 7, or deploy with `--with-registry-auth`. |
| 502 from nginx after updating a service | nginx cached the old container address. Run `docker service update --force aiet_nginx`. |
| Early connection errors in logs on first start | Normal. Swarm does not wait for dependencies; services retry until `db` and the others are ready. |
| Service starts but config or data is missing | It was scheduled on a node without the bind-mounted files. Keep the `primary` pin, or copy the files (step 9). |
| GPU services crash or ignore the GPU | `nvidia` is not the default runtime on that node (step 6), or the driver or toolkit is missing. |
| Live view does not open | The browser node's address is not in a private range, or the overlay network is broken. Confirm step 4 passes. |

### Network Architecture

Two layers run between `IP1` and `IP2`. Containers never see either address.

| Layer | Ports | Traffic Carried |
|---|---|---|
| Control plane | 2377/tcp (manager), 7946/tcp+udp | cluster membership and health: why `docker node ls` works |
| Data plane | 4789/udp (VXLAN tunnel) | all container traffic: a `chrome-node` on the worker reaching `selenium-hub` on the manager goes through this tunnel |

Containers address each other by **service name** (`selenium-hub`, `app-backend`). Swarm's built-in DNS resolves the name to a private overlay address, which is why no application setting mentions `IP1` or `IP2`.

The one exception is the public port. Swarm's routing mesh opens `NGINX_PORT` on every node and forwards to wherever `nginx` runs, so the application answers on `IP1` and on `IP2`.

## Next Steps

To set the number of browser nodes and backend copies, continue with [Scaling And Capacity](./scaling_and_capacity.md).
