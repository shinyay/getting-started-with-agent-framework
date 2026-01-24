# syntax=docker/dockerfile:1.6
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# --- OS tools + Azure CLI (apt install, Microsoft keyring) ---
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    apt-transport-https ca-certificates curl gnupg lsb-release jq git \
 && mkdir -p /etc/apt/keyrings \
 && curl -sLS https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor \
    | tee /etc/apt/keyrings/microsoft.gpg > /dev/null \
 && chmod go+r /etc/apt/keyrings/microsoft.gpg \
 && AZ_DIST=$(lsb_release -cs) \
 && printf "Types: deb\nURIs: https://packages.microsoft.com/repos/azure-cli/\nSuites: %s\nComponents: main\nArchitectures: %s\nSigned-by: /etc/apt/keyrings/microsoft.gpg\n" \
    "${AZ_DIST}" "$(dpkg --print-architecture)" \
    > /etc/apt/sources.list.d/azure-cli.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends azure-cli \
 && rm -rf /var/lib/apt/lists/*

# --- Python deps for Agent Framework demos (pinned for reproducibility) ---
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /workspaces

