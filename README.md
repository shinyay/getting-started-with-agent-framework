# Title

## Description

## Demo

## Features

- feature:1
- feature:2

## Requirement

## Usage

## Installation

## Dev Container

This repository includes a starter `.devcontainer/Dockerfile` as a foundation for creating a development environment using VS Code Dev Containers.

### What this Dockerfile is for

- **Defines the development image for the Dev Container**: It pins what gets installed inside the container (OS tools, Python runtime, CLIs, etc.).
- **Separated responsibilities from VS Code settings**: Typically, `.devcontainer/devcontainer.json` defines VS Code-side configuration (extensions, port forwarding, user settings, mounts), while the `Dockerfile` focuses on the base environment (base image + additional installs).
- **Uses `/workspaces` as the working directory**: Following Dev Containers conventions, the repository is expected to be mounted under `/workspaces` (see `WORKDIR /workspaces`).

### What the Dockerfile does (high level)

- Uses `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm` as the base image (Python **3.11** on Debian **bookworm**).
- Installs common tools (e.g., `curl`, `git`, `jq`) via apt, adds Microsoft’s official apt repository, and installs **Azure CLI** (`azure-cli`).
- Installs Python dependencies for demos/samples from `requirements.txt` (intended to be pinned for reproducibility).

### Python dependencies (`requirements.txt`)

The repository root `requirements.txt` defines the Python packages installed into the Dev Container image.

#### What this file is for

- **Reproducible demo environment**: packages are pinned (especially the Agent Framework packages) so everyone gets the same versions inside the Dev Container.
- **Pre-release support**: it includes `--pre`, allowing pip to install pre-release/beta versions when specified.
- **Runtime helpers**: includes common libraries used by the demos (e.g., OpenAI-compatible client library, dotenv loading, data models/validation).

#### Notes

- Because `--pre` is enabled and beta versions are pinned, expect more frequent changes compared to stable releases.
- If you update these versions, rebuild the Dev Container image to apply the changes.

### Notes

- This Dockerfile runs `COPY requirements.txt ...`, so the build will fail unless a `requirements.txt` exists at the repository root.
- To use “Reopen in Container” smoothly in VS Code, you typically need `.devcontainer/devcontainer.json` that references this Dockerfile.

### Docker Compose for the Dev Container

This repository also provides `.devcontainer/compose.yaml`, which defines how the Dev Container is started using Docker Compose.

#### What this compose file is for

- **Defines the runtime wiring**: how the container is built and run (service name, command, volumes, ports).
- **Connects VS Code to the Dockerfile build**: it builds the `workspace` service from `..` using `.devcontainer/Dockerfile`.
- **Keeps the container alive for development**: it runs `sleep infinity` so VS Code can attach and you can run commands interactively.

#### What it does (high level)

- Creates a single service named `workspace`.
- Builds the image from the repository root (`context: ..`) with `.devcontainer/Dockerfile`.
- Mounts the repository into the container at `/workspaces` (`..:/workspaces:cached`).
- Forwards port `8080` from the container to the host (`8080:8080`).

### VS Code Dev Container configuration (`devcontainer.json`)

`.devcontainer/devcontainer.json` is the entry point for VS Code Dev Containers. It tells VS Code **how to build, start, and customize** the development environment.

#### What this file is for

- **Selects the container runtime setup**: this configuration uses Docker Compose (`"dockerComposeFile": ["compose.yaml"]`) and attaches VS Code to the `workspace` service.
- **Defines workspace behavior**: sets the workspace folder to `/workspaces`, uses the `vscode` user, and stops Compose on shutdown (`"shutdownAction": "stopCompose"`).
- **Port forwarding UX**: forwards port `8080` and adds a friendly label/notification behavior via `portsAttributes`.
- **Developer tooling**: installs recommended VS Code extensions (Python, Pylance, Ruff, Docker).
- **Environment variables**: passes through Azure-related variables from your local environment into the container via `containerEnv`.

#### Notes

- `postCreateCommand` references `.devcontainer/postCreateCommand.sh`. Make sure this script exists (and is executable) if you want post-create setup to run.
- The Azure variables in `containerEnv` are read from your host environment (`${localEnv:...}`). You may want to provide them via a local `.env` file or your shell environment before starting the Dev Container.

### Post-create setup (`postCreateCommand.sh`)

`.devcontainer/postCreateCommand.sh` is executed by VS Code after the container is created (via the `postCreateCommand` setting in `devcontainer.json`).

#### What this script is for

- **One-time container initialization**: a place to run setup steps that should happen after the workspace is mounted (e.g., creating local config files, preparing folders, printing helpful next steps).
- **Local configuration bootstrapping**: it optionally creates a `.env` file from `.env.example` if present.
- **Developer guidance**: it prints suggested next commands (Azure login, running demos, starting the DevUI on port 8080).

#### Notes

- The script uses `set -euo pipefail`, so it will fail fast on errors, unset variables, or pipeline failures.
- `.env.example` is optional; if you prefer, you can create `.env` manually (do not commit secrets).

## References

## Licence

Released under the [MIT license](https://gist.githubusercontent.com/shinyay/56e54ee4c0e22db8211e05e70a63247e/raw/f3ac65a05ed8c8ea70b653875ccac0c6dbc10ba1/LICENSE)

## Author

- github: <https://github.com/shinyay>
- twitter: <https://twitter.com/yanashin18618>
- mastodon: <https://mastodon.social/@yanashin>
