# GPU Setup

This page explains how to prepare the model-serving infrastructure required by the AI Evaluation Tool. It covers local Ollama setup, Sarvam AI service startup, remote GPU port forwarding, and the environment variables used by the CLI pipeline.

## Why GPU Setup Matters

Many evaluation strategies depend on model inference endpoints. These may be served locally, on the same machine as the CLI, or remotely on a dedicated GPU host.

## Required Judge And Service Models

The following models are required for the standard LLM-as-judge flow:

- `sarvamai/sarvam-2b-v0.5`
- `google/shieldgemma-2b`
- `sarvamai/sarvam-translate`
- `qwen3:32b`

## Default Ports

- Ollama default port: `11434`
- Sarvam AI service port: configurable

## Option 1: Local Serving

Use this setup when the CLI, Ollama, and Sarvam AI service all run on the same machine.

### Start Sarvam AI

```bash
cd src/app/sarvam_ai
python main.py --port <free-port-local>
```

### Sarvam AI CLI Arguments

`src/app/sarvam_ai/main.py` supports the following service arguments:

- `--port` or `-p`: Port exposed by the FastAPI service. Default is `16000`.
- `--host` or `-H`: Host address for the service. Default is `0.0.0.0`.
- `--verbosity` or `-v`: Logging verbosity from `0` to `5`. Default is `5`.
- `--translator-model` or `-t`: Translation model identifier. Default is `sarvamai/sarvam-translate`.
- `--generator-model` or `-g`: Text generation model identifier. Default is `sarvamai/sarvam-2b-v0.5`.
- `--safety-model` or `-s`: Safety model identifier. Default is `google/shieldgemma-2b`.
- `--force-cpu`: Forces CPU execution for the translator model.

Example with more explicit options:

```bash
python main.py \
  --host 0.0.0.0 \
  --port 16000 \
  --verbosity 5 \
  --translator-model sarvamai/sarvam-translate \
  --generator-model sarvamai/sarvam-2b-v0.5 \
  --safety-model google/shieldgemma-2b
```

### Pull And Serve The Judge Model

```bash
ollama pull qwen3:32b
ollama serve
```

In many local environments, `ollama serve` may already be active as a background service.

### Environment Variables

```env
OLLAMA_URL="http://localhost:11434"
GPU_URL="http://localhost:<free-port-local>"
LLM_AS_JUDGE_MODEL="qwen3:32b"
```

## Option 2: Remote GPU Serving With Port Forwarding

Use this setup when model-serving runs on a remote GPU host but the CLI is executed locally.

### Start Services On The Remote Machine

On the GPU host:

```bash
cd src/app/sarvam_ai
python main.py --port <free-port-gpu>
```

The same Sarvam AI flags listed above can be used here as well if you need a non-default host, different logging level, or custom model identifiers.

```bash
ollama pull qwen3:32b
```

### Forward Ports To Your Local Machine

```bash
ssh gpu_machine_cred@machineIP \
  -L 21434:localhost:11434 \
  -L <free-local-port>:localhost:<ollama-port> \
  -L <free-local-port>:localhost:<gpu-port>
```

### Local Environment Variables

After port forwarding, point your local `.env` file to the forwarded ports:

```env
OLLAMA_URL="http://localhost:21434"
GPU_URL="http://localhost:<free-local-port>"
LLM_AS_JUDGE_MODEL="qwen3:32b"
```

## Docker-Based GPU Endpoint Setup

If you run the CLI through Docker Compose, the environment values typically point to `host.docker.internal` so containers can reach host services.

### Same Machine GPU Reachability

```env
OLLAMA_URL="http://host.docker.internal:11434/"
GPU_URL="http://host.docker.internal:16000/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

### Remote GPU With Docker Port Forwarding

Example tunnel:

```bash
ssh <user>@<remote-gpu-host> \
  -L <free-local-1>:localhost:11434 \
  -L <free-local-2>:localhost:16000
```

Then set:

```env
OLLAMA_URL="http://host.docker.internal:<free-local-1>/"
GPU_URL="http://host.docker.internal:<free-local-2>/"
LLM_AS_JUDGE_MODEL="qwen3:32b"
SARVAM_API_KEY=""
OPENAI_API_KEY=""
```

## Additional Models Downloaded During Execution

The following smaller models may also be downloaded as part of runtime evaluation:

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

- Ollama endpoint responds
- Sarvam AI endpoint responds
- `.env` values match the running endpoints
- firewall and SSH forwarding allow traffic
- CLI machine can reach both `OLLAMA_URL` and `GPU_URL`

When the service starts correctly, the startup logs should look similar to:

```text
[INFO] Loading models...
[INFO] Loading sarvamai/sarvam-2b-v0.5...
[INFO] Loading google/shieldgemma-2b...
[INFO] Loading sarvamai/sarvam-translate...
[INFO] All models loaded successfully
[INFO] Sarvam AI Service running on http://0.0.0.0:16000
[INFO] Ready to serve evaluation requests
```
