import os
import shutil
import socket
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import HostedCodeInterpreterTool, HostedWebSearchTool, MCPStdioTool, WorkflowBuilder
from agent_framework.azure import AzureAIAgentClient
from dotenv import dotenv_values
from azure.identity.aio import AzureCliCredential


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers / Codespaces, vars may be injected as empty strings.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOTENV_PATH = _REPO_ROOT / ".env"
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
            "If your Foundry project uses private networking / private DNS, run this demo from a network that can resolve the private endpoint, "
            "or switch to a public (non-private-link) project endpoint."
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
    """Build HostedWebSearchTool configuration.

    We accept either the env var names referenced by the Agent Framework runtime
    or the names commonly used in Foundry docs.
    """

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
        "You can create a 'Grounding with Bing Search' connection in the Foundry portal, then copy its project connection ID."
    )

def _validate_environment() -> None:
    """Validate runtime requirements.

    NOTE: We intentionally do *not* run this at import time so DevUI can start
    and list entities even when env vars are not configured yet.
    """

    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()
    _require_command("npx")


@lru_cache(maxsize=1)
def _get_client() -> AzureAIAgentClient:
    """Create and cache a single AzureAIAgentClient for the process."""

    # We pass explicit config so failures are easier to reason about in DevUI.
    project_endpoint = _require_env("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment_name = _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")

    # NOTE: This SDK expects an async credential type.
    cred = AzureCliCredential()

    return AzureAIAgentClient(
        credential=cred,
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment_name,
    )


def create_coordinator_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="coordinator",
        instructions=(
            "You are the Event Coordinator, the workflow orchestrator for event planning. "
            "Use the sequential-thinking tool to break down tasks into clear steps before proceeding."
        ),
        tools=[
            MCPStdioTool(
                name="sequential-thinking",
                command="npx",
                load_prompts=False,
                args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
            )
        ],
    )


def create_venue_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="venue",
        instructions=(
            "You are the Venue Specialist. Recommend venues for the event and justify your choices. "
            "Consider capacity, location, accessibility, amenities, and vibe."
        ),
        tools=[
            HostedWebSearchTool(
                description="Search the web for current information using Bing",
                tool_properties=_get_bing_tool_properties(),
            )
        ],
    )


def create_catering_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="catering",
        instructions=(
            "You are the Catering Coordinator. Propose food & beverage options for the event. "
            "Include options for common dietary restrictions by default, and match the plan to the venue and schedule."
        ),
        tools=[
            HostedWebSearchTool(
                description="Search the web for current information using Bing",
                tool_properties=_get_bing_tool_properties(),
            )
        ],
    )


def create_budget_analyst_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="budget_analyst",
        instructions=(
            "You are the Budget Analyst. Create a reasonable per-person estimate and allocate costs across venue, catering, AV, staffing, and contingency. "
            "When you need calculations, use the code interpreter tool."
        ),
        tools=[
            HostedCodeInterpreterTool(
                description=(
                    "Execute Python code for calculations: budget breakdowns, totals, per-person estimates, and simple what-if analysis."
                )
            )
        ],
    )


def create_booking_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="booking",
        instructions=(
            "You are the Event Booking Specialist. Synthesize all prior specialist outputs into one cohesive event plan. "
            "Use markdown headings and bullet points. Include an executive summary, venue, catering, budget, logistics, and next steps."
        ),
    )


workflow = (
    WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
    .register_agent(create_coordinator_agent, "coordinator")
    .register_agent(create_venue_agent, "venue")
    .register_agent(create_catering_agent, "catering")
    .register_agent(create_budget_analyst_agent, "budget_analyst")
    .register_agent(create_booking_agent, "booking", output_response=True)
    .set_start_executor("coordinator")
    .add_edge("coordinator", "venue")
    .add_edge("venue", "catering")
    .add_edge("catering", "budget_analyst")
    .add_edge("budget_analyst", "booking")
    .build()
)
