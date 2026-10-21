# Docker Run

Docker is the quickest way to run the whole AI Evaluation Tool: the database, browser automation, interface manager, backends and both web interfaces start together with one command, the same way on every machine.

## When To Use Docker

- you want a working setup without installing each service by hand
- several people need the same environment
- you want the same layout as a production deployment, behind one address

For a local setup without Docker, see [UI Setup](../ui/setup.md) or the [CLI Initial Setup](../cli/initial_setup_and_configuration.md).

## Models And GPUs

Docker runs the evaluation services. The model servers (Ollama and Sarvam AI) can run in Docker on a machine with an NVIDIA GPU, or on a separate GPU server that the containers reach over the network. The machine needs 64 GB of CPU RAM, and 30 GB of GPU VRAM for the default judge model (60 GB if Sarvam AI also runs on the GPU). See [System Requirements](../docker_setup/setup_and_configuration.md#system-requirements).

## Where To Go Next

- [Docker Setup](../docker_setup/index.md): quick start, services and ports
- [Setup And Configuration](../docker_setup/setup_and_configuration.md): every setting and its default
- [GPU Setup](../docker_setup/gpu_setup.md): bundled or remote model services
