# GPU Setup

This page documents the Docker-oriented GPU setup patterns for the AI Evaluation Tool.

The key goal is to make both of these endpoints reachable from Dockerized runtime containers (`app-backend` and related services):

- `OLLAMA_URL`
- `GPU_URL`

Once both endpoints are reachable from inside Docker, the rest of the pipeline stays the same.

## Required Models

The README identifies these primary models for the LLM-as-judge and supporting evaluation flow:

1. `sarvamai/sarvam-2b-v0.5`
2. `google/shieldgemma-2b`
3. `sarvamai/sarvam-translate`
4. `qwen3:32b`

## Compose-Managed Production Model Services

Use the `prod` profile when you want Docker Compose to start the production model-serving services:

- `ollama`
- `ollama-init`
- `ollama-warmup`
- `sarvam-ai`

```bash
docker compose --profile prod up -d --build
```

For this mode, use Compose service names in `.env`:

```env
OLLAMA_URL="http://ollama:11434/"
GPU_URL="http://sarvam-ai:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
```

The `ollama-init` service pulls `${OLLAMA_MODEL:-qwen3:32b}` and `ollama-warmup` verifies that Ollama can generate a response.

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
