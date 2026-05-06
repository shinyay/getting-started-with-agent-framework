# Exercise 6: DevUI Entity — Workflow Definition (simplified 3-agent version)
# Solution reference: entities/event_planning_workflow/workflow.py

import os
import shutil
import socket
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import WorkflowBuilder
from agent_framework.foundry import FoundryChatClient
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
    endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    host = urlparse(endpoint).hostname
    if not host:
        raise RuntimeError(
            "FOUNDRY_PROJECT_ENDPOINT does not look like a valid URL. "
            f"Got: {endpoint}"
        )
    try:
        socket.getaddrinfo(host, 443)
    except OSError as ex:
        raise RuntimeError(
            "Cannot resolve FOUNDRY_PROJECT_ENDPOINT host via DNS from this environment.\n\n"
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
    """Build Foundry web search tool configuration."""
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
    _require_env("FOUNDRY_PROJECT_ENDPOINT")
    _require_env("FOUNDRY_MODEL")
    _check_project_endpoint_dns()


@lru_cache(maxsize=1)
def _get_client() -> FoundryChatClient:
    """Create and cache a single FoundryChatClient for the process."""
    project_endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    model_deployment_name = _require_env("FOUNDRY_MODEL")
    cred = AzureCliCredential()
    return FoundryChatClient(
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
#   - Returns client.as_agent() with a hosted web search tool
#
#   Hint (Agent Framework 1.2.2):
#     tools=[
#         client.get_web_search_tool(
#             custom_search_configuration=_get_bing_tool_properties(),
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
# TODO(4): Materialize the agents at module load time
#   In Agent Framework 1.2.2, WorkflowBuilder needs actual Executor /
#   SupportsAgentRun instances (not factory function references), so call
#   each create_xxx_agent() once here:
#     _coordinator = create_coordinator_agent()
#     _venue = create_venue_agent()
#     _booking = create_booking_agent()
#
# TODO(5): Build the workflow using WorkflowBuilder
#   Pass `start_executor=_coordinator` and `output_executors=[_booking]` to
#   the constructor (these are required keyword args in 1.2.2):
#     WorkflowBuilder(
#         name="Event Planning Workflow",
#         max_iterations=30,
#         start_executor=_coordinator,
#         output_executors=[_booking],
#     )
#
# TODO(6): Add edges: coordinator → venue → booking, then .build()
#     .add_edge(_coordinator, _venue)
#     .add_edge(_venue, _booking)
#     .build()
# ----------------------------------------------------------------
workflow = None  # Replace with WorkflowBuilder chain
