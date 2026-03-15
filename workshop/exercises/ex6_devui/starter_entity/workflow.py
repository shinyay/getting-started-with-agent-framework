# Exercise 6: DevUI Entity — Workflow Definition (simplified 3-agent version)
# Solution reference: entities/event_planning_workflow/workflow.py

import os
import shutil
import socket
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import HostedWebSearchTool, WorkflowBuilder
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values


# ---------------------------------------------------------------------------
# .env loading (fill-only — never overwrite existing non-empty values)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[4]
_DOTENV_PATH = _REPO_ROOT / ".env"
_dotenv = dotenv_values(_DOTENV_PATH)
for _k, _v in _dotenv.items():
    if _v is None:
        continue
    _existing = os.getenv(_k)
    if _existing is None or not _existing.strip():
        os.environ[_k] = _v


# ---------------------------------------------------------------------------
# Helper utilities (provided — no changes needed)
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}. "
            "Set it via .env / export / Codespaces secrets and try again."
        )
    return value


def _check_project_endpoint_dns() -> None:
    endpoint = _require_env("AZURE_AI_PROJECT_ENDPOINT")
    host = urlparse(endpoint).hostname
    if not host:
        raise RuntimeError(
            "AZURE_AI_PROJECT_ENDPOINT does not look like a valid URL. "
            f"Got: {endpoint}"
        )
    try:
        socket.getaddrinfo(host, 443)
    except OSError as ex:
        raise RuntimeError(
            "Cannot resolve AZURE_AI_PROJECT_ENDPOINT host via DNS from this environment.\n\n"
            f"  Host: {host}\n"
            f"  Endpoint: {endpoint}\n\n"
            "If your Foundry project uses private networking / private DNS, run this demo from "
            "a network that can resolve the private endpoint, or switch to a public (non-private-link) "
            "project endpoint."
        ) from ex


def _require_command(cmd: str) -> str:
    resolved = shutil.which(cmd)
    if not resolved:
        raise RuntimeError(
            f"Required command is not available on PATH: {cmd}.\n\n"
            "This workflow uses a local MCP server launched via Node.js (npx).\n"
            "In this dev container, node/npx are typically preinstalled. "
            "If you're running elsewhere, install Node.js and try again."
        )
    return resolved


@lru_cache(maxsize=1)
def _get_bing_tool_properties() -> dict:
    """Build HostedWebSearchTool configuration."""
    connection_id = (
        os.getenv("BING_CONNECTION_ID")
        or os.getenv("BING_PROJECT_CONNECTION_ID")
        or ""
    ).strip()
    if connection_id:
        return {"connection_id": connection_id}

    custom_connection_id = (
        os.getenv("BING_CUSTOM_CONNECTION_ID")
        or os.getenv("BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID")
        or ""
    ).strip()
    custom_instance_name = (
        os.getenv("BING_CUSTOM_INSTANCE_NAME")
        or os.getenv("BING_CUSTOM_SEARCH_INSTANCE_NAME")
        or ""
    ).strip()
    if custom_connection_id and custom_instance_name:
        return {
            "custom_connection_id": custom_connection_id,
            "custom_instance_name": custom_instance_name,
        }

    raise RuntimeError(
        "Hosted web search requires a Bing connection. Set either:\n"
        "  - BING_CONNECTION_ID (or BING_PROJECT_CONNECTION_ID)\n"
        "  - OR BING_CUSTOM_CONNECTION_ID + BING_CUSTOM_INSTANCE_NAME\n"
        "    (or BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID + BING_CUSTOM_SEARCH_INSTANCE_NAME)\n\n"
        "You can create a 'Grounding with Bing Search' connection in the Foundry portal, "
        "then copy its project connection ID."
    )


def _validate_environment() -> None:
    """Validate runtime requirements.

    NOTE: We intentionally do *not* run this at import time so DevUI can start
    and list entities even when env vars are not configured yet.
    """
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()


@lru_cache(maxsize=1)
def _get_client() -> AzureAIAgentClient:
    """Create and cache a single AzureAIAgentClient for the process."""
    project_endpoint = _require_env("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment_name = _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    cred = AzureCliCredential()
    return AzureAIAgentClient(
        credential=cred,
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
    )


# ---------------------------------------------------------------------------
# Agent factory functions
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------
# TODO(1): Create coordinator factory function
#   Define create_coordinator_agent() that:
#   - Calls _validate_environment()
#   - Gets the client via _get_client()
#   - Returns client.as_agent(name="coordinator", instructions="...")
#
#   Example instructions: "You are the Event Coordinator. Break down event
#   planning tasks into clear steps for the other specialists."
# ----------------------------------------------------------------
...


# ----------------------------------------------------------------
# TODO(2): Create venue factory function
#   Define create_venue_agent() that:
#   - Calls _validate_environment() and _get_client()
#   - Returns client.as_agent() with HostedWebSearchTool
#
#   Hint:
#     tools=[
#         HostedWebSearchTool(
#             description="Search the web for current information using Bing",
#             tool_properties=_get_bing_tool_properties(),
#         )
#     ]
# ----------------------------------------------------------------
...


# ----------------------------------------------------------------
# TODO(3): Create booking factory function
#   Define create_booking_agent() that:
#   - Calls _validate_environment() and _get_client()
#   - Returns client.as_agent() with no tools
#
#   This agent synthesizes all prior specialist outputs into one
#   cohesive event plan with markdown formatting.
# ----------------------------------------------------------------
...


# ---------------------------------------------------------------------------
# Workflow definition
# ---------------------------------------------------------------------------

# ----------------------------------------------------------------
# TODO(4): Build the workflow using WorkflowBuilder
#   Use WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
#   Chain .register_agent(factory_fn, "name") for each agent
#   The last agent (booking) should have output_response=True
#
# TODO(5): Set start executor to coordinator
#   Chain .set_start_executor("coordinator")
#
# TODO(6): Add edges: coordinator → venue → booking, then .build()
#   Chain .add_edge("coordinator", "venue")
#         .add_edge("venue", "booking")
#         .build()
# ----------------------------------------------------------------
workflow = None  # Replace with WorkflowBuilder chain
