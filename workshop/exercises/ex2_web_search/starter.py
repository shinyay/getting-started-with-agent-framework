# Exercise 2: Add Hosted Web Search Tool
#
# In this exercise you will add a Bing-backed web search tool to an agent.
# The helper code (.env loading, DNS check, Bing configuration) is provided.
#
# Fill in the 3 TODOs inside async def main() to complete the exercise.
# Then run:  python workshop/exercises/ex2_web_search/starter.py

import asyncio
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import HostedWebSearchTool
from agent_framework.exceptions import ServiceResponseException
from agent_framework.azure import AzureAIAgentClient
from dotenv import dotenv_values
from azure.identity.aio import AzureCliCredential


# Optional: emit concise OpenTelemetry lines for agent/tool spans.
# (If OpenTelemetry isn't available in your environment, we skip this.)
try:
    from agent_framework.observability import configure_otel_providers
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
except Exception:  # pragma: no cover
    configure_otel_providers = None  # type: ignore[assignment]
    SpanExporter = object  # type: ignore[misc,assignment]
    SpanExportResult = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# .env loading  (fills only missing/empty env vars — does not overwrite)
# ---------------------------------------------------------------------------
_DOTENV_PATH = Path(__file__).resolve().parents[3] / ".env"

_dotenv = dotenv_values(_DOTENV_PATH)
for _k, _v in _dotenv.items():
    if _v is None:
        continue
    _existing = os.getenv(_k)
    if _existing is None or not _existing.strip():
        os.environ[_k] = _v


# ---------------------------------------------------------------------------
# Helpers (provided — you do NOT need to modify these)
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}. "
            "Set it via .env / export / Codespaces secrets and try again."
        )
    return value


def _get_bing_tool_properties() -> dict:
    """Build HostedWebSearchTool configuration.

    Azure AI Foundry's hosted web search capability is backed by Bing grounding.
    The Agent Framework runtime requires either:
      - 'connection_id' (Grounding with Bing Search)
      - or 'custom_connection_id' + 'custom_instance_name' (Bing Custom Search)

    The library error message references env vars:
      - BING_CONNECTION_ID
      - BING_CUSTOM_CONNECTION_ID
      - BING_CUSTOM_INSTANCE_NAME

    Foundry documentation commonly refers to:
      - BING_PROJECT_CONNECTION_ID
      - BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID
      - BING_CUSTOM_SEARCH_INSTANCE_NAME

    We accept both sets for convenience.
    """

    # Standard Bing grounding
    connection_id = (os.getenv("BING_CONNECTION_ID") or os.getenv("BING_PROJECT_CONNECTION_ID") or "").strip()
    if connection_id:
        return {"connection_id": connection_id}

    # Custom Bing Search
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


def _check_project_endpoint_dns() -> None:
    """Fail fast if the Foundry project endpoint hostname cannot be resolved."""

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


class _DemoSpanExporter(SpanExporter):
    """Print one concise line per span (agent runs + tool calls)."""

    def export(self, spans):  # type: ignore[override]
        if SpanExportResult is None:
            return None

        for s in spans:
            attrs = dict(getattr(s, "attributes", None) or {})
            is_agent = "gen_ai.agent.name" in attrs or str(s.name).startswith("invoke_agent")
            is_tool = (
                "gen_ai.tool.name" in attrs
                or "gen_ai.tool.call.id" in attrs
                or "tool.name" in attrs
                or "function.name" in attrs
                or str(s.name).startswith(("run_tool", "invoke_tool"))
            )
            if not (is_agent or is_tool):
                continue

            agent = attrs.get("gen_ai.agent.name") or attrs.get("agent.name") or "-"
            tool = (
                attrs.get("gen_ai.tool.name")
                or attrs.get("tool.name")
                or attrs.get("function.name")
                or "-"
            )
            op = attrs.get("gen_ai.operation.name") or attrs.get("operation.name") or "-"
            kind = "TOOL" if is_tool else "AGENT"
            print(f"[{kind}] name={s.name!s} op={op} agent={agent} tool={tool}")

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Main — fill in the 3 TODOs below
# ---------------------------------------------------------------------------

async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()
    bing_props = _get_bing_tool_properties()

    async with AzureCliCredential() as cred:

        # TODO(1): Create a HostedWebSearchTool with additional_properties
        #          that includes user_location and bing_props.
        #
        # Example user_location: {"city": "Seattle", "country": "US"}
        # Use **bing_props to merge the Bing connection config into
        # additional_properties alongside user_location.

        # TODO(2): Create an agent using AzureAIAgentClient(credential=cred).as_agent()
        #          with name, instructions mentioning web search, and tools=[your_tool].
        #
        # Remember to use `async with ... as agent:` so the agent is cleaned up.
        # Example instructions:
        #   "You are a web search expert who can find current information on the web
        #    to help plan events and answer questions."

        # TODO(3): Call agent.run() with a search query and print result.text.
        #
        # Wrap the call in try/except for graceful error handling:
        #
        #   try:
        #       result = await agent.run("your search query here")
        #   except ServiceResponseException as ex:
        #       msg = str(ex)
        #       if "Failed to resolve model info" in msg:
        #           raise RuntimeError(
        #               "Could not resolve model deployment. "
        #               "Check AZURE_AI_MODEL_DEPLOYMENT_NAME in the Foundry portal."
        #           ) from ex
        #       raise
        #
        #   print(result.text)

        pass  # Remove this line once you've filled in the TODOs


if __name__ == "__main__":
    if configure_otel_providers is not None:
        configure_otel_providers(exporters=[_DemoSpanExporter()])
    asyncio.run(main())
