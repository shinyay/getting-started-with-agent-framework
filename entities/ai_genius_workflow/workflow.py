"""DevUI workflow entity: Writer -> Reviewer.

This is intentionally import-friendly: DevUI discovers this module and expects a
module-level variable named `workflow`.

We use Azure OpenAI (Demo 1) here for stability inside DevUI.
"""

import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import dotenv_values


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers / Codespaces, vars may be injected as empty strings.
_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"
_dotenv = dotenv_values(_DOTENV_PATH)
for _k, _v in _dotenv.items():
    if _v is None:
        continue
    _existing = os.getenv(_k)
    if _existing is None or not _existing.strip():
        os.environ[_k] = _v


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}. "
            "Set it via .env / export / Codespaces secrets and try again."
        )
    return value


def _check_endpoint_dns(url: str, env_name: str) -> None:
    host = urlparse(url).hostname
    if not host:
        raise RuntimeError(f"{env_name} does not look like a valid URL: {url}")
    socket.getaddrinfo(host, 443)


# Demo 1 env vars
_endpoint = _require_env("AZURE_OPENAI_ENDPOINT")
_deployment = _require_env("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
_api_version = (os.getenv("AZURE_OPENAI_API_VERSION") or "").strip() or None

_check_endpoint_dns(_endpoint, "AZURE_OPENAI_ENDPOINT")

# Entra ID (Azure CLI credential) is the default for this repository.
# Import lazily so DevUI discovery doesn't require azure-identity unless used.
from azure.identity import AzureCliCredential  # noqa: E402

_client = AzureOpenAIChatClient(
    credential=AzureCliCredential(),
    # Explicitly avoid key auth by default.
    api_key="",
    endpoint=_endpoint,
    deployment_name=_deployment,
    api_version=_api_version,
)

writer = _client.as_agent(
    name="Writer",
    instructions="You are an excellent content writer. Generate a short draft based on the request.",
)

reviewer = _client.as_agent(
    name="Reviewer",
    instructions="You are an excellent reviewer. Give concise, actionable feedback.",
)

workflow = WorkflowBuilder().set_start_executor(writer).add_edge(writer, reviewer).build()
