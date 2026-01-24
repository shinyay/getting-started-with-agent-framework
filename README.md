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

## References

## Licence

Released under the [MIT license](https://gist.githubusercontent.com/shinyay/56e54ee4c0e22db8211e05e70a63247e/raw/f3ac65a05ed8c8ea70b653875ccac0c6dbc10ba1/LICENSE)

## Author

- github: <https://github.com/shinyay>
- twitter: <https://twitter.com/yanashin18618>
- mastodon: <https://mastodon.social/@yanashin>
