# GPU Setup

This page documents the Docker-oriented GPU setup patterns for the AI Evaluation Tool.

The key goal is to make both of these endpoints reachable from Dockerized runtime containers (`app-backend` and related services):

- `OLLAMA_URL`
- `GPU_URL`

Once both endpoints are reachable from inside Docker, the rest of the pipeline stays the same.

## Hardware Needed

The machine that runs the models needs **64 GB of CPU RAM** and at least **30 GB of GPU VRAM** for the default judge model `qwen3:32b`, or **60 GB** if Sarvam AI also runs on the GPU. The full list, with disk, CPU and software, is in [System Requirements](./setup_and_configuration.md#system-requirements).

## Required Models

The README identifies these primary models for the LLM-as-judge and supporting evaluation flow:

1. `sarvamai/sarvam-2b-v0.5`
2. `google/shieldgemma-2b`
3. `sarvamai/sarvam-translate`
4. `qwen3:32b`

## Install NVIDIA Container Toolkit And Set The Docker Runtime

Docker containers can use the GPU only if the NVIDIA driver and the NVIDIA Container Toolkit are installed on the host, and Docker is set up to use the `nvidia` runtime. This is needed for every setup on this page that runs `ollama` or `sarvam-ai` in Docker (`--profile prod` or `--profile sarvam`). Skip it if the model services run on another machine, and do it on that machine instead.

The commands below are for Ubuntu and Debian. For other distributions, follow NVIDIA's [Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

> **Note:** these commands were correct when this page was written. NVIDIA can change the repository address, package names or steps. If a command fails or behaves differently, check NVIDIA's official [Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and follow it instead.

### 1. Check What Is Already Done

```bash
nvidia-smi
nvidia-ctk --version
docker info | grep -i runtime
```

| Result | Meaning |
|---|---|
| `nvidia-smi` fails | the NVIDIA driver is not installed. Install it first and reboot; the toolkit does not include the driver |
| `nvidia-ctk: command not found` | the toolkit is not installed. Do step 2 |
| `Runtimes:` lists `nvidia` | the runtime is registered. Do step 3 only if `Default Runtime` is not `nvidia` and you need it (multi-node Swarm) |
| `Runtimes:` has no `nvidia` | the runtime is not configured. Do step 3 |

If the last check in [step 4](#4-verify-that-containers-see-the-gpu) already passes, there is nothing to do.

### 2. Install The Toolkit

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### 3. Set Docker To Use The `nvidia` Runtime

```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

This registers the `nvidia` runtime in `/etc/docker/daemon.json`. Restarting Docker stops the running containers, so do it before you start the stack, or run `docker compose up -d` again afterwards.

Plain `docker compose` uses the GPU reservation in the compose file and does not need `nvidia` as the default runtime. In a multi-node Docker Swarm, the reservation is not honoured reliably, so also make `nvidia` the default runtime on every GPU machine:

```bash
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
sudo systemctl restart docker
```

See [Multi-Node Stack](./multi_node_stack.md#6-make-nvidia-the-default-runtime-gpu-machines).

### 4. Verify That Containers See The GPU

```bash
docker run --rm --gpus all ubuntu nvidia-smi
```

It must print the same GPU table as `nvidia-smi` on the host. If it fails:

| Error | Fix |
|---|---|
| `could not select device driver "" with capabilities: [[gpu]]` | the toolkit is not installed or Docker was not restarted. Repeat steps 2 and 3 |
| `unknown or invalid runtime name: nvidia` | `/etc/docker/daemon.json` has no `nvidia` entry. Run the `nvidia-ctk runtime configure` command again and restart Docker |
| `nvidia-smi` works on the host but not in the container | check that `daemon.json` is valid JSON, and restart Docker again |

## Compose-Managed Production Model Services

Use the `prod` profile when you want Docker Compose to start the production model-serving services:

- `ollama`
- `ollama-init`
- `ollama-warmup`
- `sarvam-ai`

```bash
docker compose --profile prod up -d
```

For this mode, use Compose service names in `.env`:

```env
OLLAMA_URL="http://ollama:11434/"
GPU_URL="http://sarvam-ai:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
```

The `ollama-init` service pulls `${LLM_AS_JUDGE_MODEL:-qwen3:32b}` and `ollama-warmup` verifies that Ollama can generate a response.

`qwen3:32b` is the default judge model. To use another Ollama model, set `LLM_AS_JUDGE_MODEL`; the bundled Ollama pulls that same model. Results and speed vary by model.

## Local Host GPU Setup

Use this setup when the Docker machine and the GPU machine are the same host, but Ollama or Sarvam AI are served outside the main production profile.

This is the simplest arrangement: Ollama runs on the host and Sarvam AI can either run as a Compose profile or as another reachable endpoint.

### Serve Ollama On The Host

```bash
ollama pull qwen3:32b
ollama serve
```

### Option A: Use Compose-Managed Sarvam AI (Recommended)

```bash
docker compose --profile sarvam up -d sarvam-ai
```

Then set in `.env`:

```env
GPU_URL="http://sarvam-ai:16000/"
```

### Option B: Use Host-Served Sarvam Endpoint

If Sarvam is running on the Docker host directly, use:

```env
GPU_URL="http://host.docker.internal:16000/"
```

### Set Common `.env` Model Values

```env
OLLAMA_URL="http://host.docker.internal:11434/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

## Remote GPU Setup

Use this setup when evaluation commands are run locally, but the actual model serving happens on a separate GPU host.

### Serve Ollama On The Remote GPU Machine

```bash
ollama pull qwen3:32b
ollama serve
```

Sarvam AI should also be running on that remote GPU host and exposed on port `16000`.

### Forward The Remote Ports To The Local Machine

From your local machine, create SSH tunnels to both the Ollama port and the Sarvam AI port:

```bash
ssh <user>@<remote-gpu-host> \
  -L 21434:localhost:11434 \
  -L 16000:localhost:16000
```

Once those tunnels are active, the forwarded ports behave like local host ports from Docker’s point of view.

### Point Local Docker Containers To The Forwarded Ports

Set in `.env`:

```env
OLLAMA_URL="http://host.docker.internal:21434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

## Notes On Reachability

- `OLLAMA_URL` is used by LLM-as-judge and related local-LLM strategies.
- `GPU_URL` is used by strategy modules that call the Sarvam AI or GPU inference API.
- both endpoints must be reachable from inside Docker containers

If either endpoint is wrong, the workflow usually fails later during execution or analysis, so this is a good place to validate connectivity early.

## Additional Models Downloaded During Runtime

The README also notes that these smaller models may be downloaded during execution:

- `amedvedev/bert-tiny-cognitive-bias`
- `LibrAI/longformer-harmful-ro`
- `vectara/hallucination_evaluation_model`
- `thenlper/gte-small`
- `all-MiniLM-L6-v2`
- `nicholasKluge/ToxiGuardrail`
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- `google/flan-t5-large`
- `holistic-ai/bias_classifier_albertv2`
- `Human-CentricAI/LLM-Refusal-Classifier`
- `cross-encoder/nli-deberta-base`

## Validation Checklist

- Ollama is reachable
- Sarvam AI is reachable
- `.env` values match the actual ports
- profile-specific URLs are correct (`ollama`/`sarvam-ai` inside Compose, `host.docker.internal` for host-served endpoints)
- SSH tunneling is active for remote setups
- Docker services can resolve `host.docker.internal`
