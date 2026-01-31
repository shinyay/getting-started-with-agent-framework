import asyncio
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient
from agent_framework.exceptions import ServiceResponseException
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values
from pydantic import BaseModel


# Optional: emit concise OpenTelemetry lines for agent/tool spans.
# (If OpenTelemetry isn't available in your environment, we skip this.)
try:
    from agent_framework.observability import configure_otel_providers
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
except Exception:  # pragma: no cover
    configure_otel_providers = None  # type: ignore[assignment]
    SpanExporter = object  # type: ignore[misc,assignment]
    SpanExportResult = None  # type: ignore[assignment]


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers / Codespaces, vars may be injected as empty strings.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
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
    connection_id = (
        os.getenv("BING_CONNECTION_ID")
        or os.getenv("BING_PROJECT_CONNECTION_ID")
        or ""
    ).strip()
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


class VenueInfoModel(BaseModel):
    """Information about a venue."""

    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0


class VenueOptionsModel(BaseModel):
    """Options for a venue."""

    options: list[VenueInfoModel]


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


async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()
    bing_props = _get_bing_tool_properties()

    print("=" * 80)
    print("Demo 4: Structured Output (response_format) with Web Search")
    print("=" * 80)

    async with AzureCliCredential() as cred:
        print("Creating client...")
        async with AzureAIAgentClient(credential=cred) as client:
            print("Creating agent...")
            async with client.as_agent(
                name="venue_specialist",
                instructions=(
                    "You are the Venue Specialist, an expert in venue research and recommendation. "
                    "Use web search to find venue options and return only structured data that matches the provided schema."
                ),
                tools=[
                    HostedWebSearchTool(
                        additional_properties={
                            "user_location": {"city": "Seattle", "country": "US"},
                            **bing_props,
                        }
                    )
                ],
            ) as agent:
                print("Running agent...")
                try:
                    response = await agent.run(
                        "Find venue options for a corporate holiday party for 50 people on December 6th, 2026 in Seattle",
                        response_format=VenueOptionsModel,
                    )
                except ServiceResponseException as ex:
                    msg = str(ex)
                    if "Failed to resolve model info" in msg:
                        raise RuntimeError(
                            "Azure AI Foundry could not resolve the model deployment specified by AZURE_AI_MODEL_DEPLOYMENT_NAME.\n\n"
                            "What to check:\n"
                            "- In the Foundry portal for this project, open 'Models + endpoints' and confirm the deployment name exists.\n"
                            "- AZURE_AI_MODEL_DEPLOYMENT_NAME must be the Foundry project model deployment name.\n\n"
                            "Current value:\n"
                            f"  AZURE_AI_MODEL_DEPLOYMENT_NAME={os.environ.get('AZURE_AI_MODEL_DEPLOYMENT_NAME','')}\n"
                        ) from ex
                    raise

                venue_options = getattr(response, "value", None)
                if venue_options:
                    print("Result:")
                    for option in venue_options.options:
                        print(
                            "\n".join(
                                [
                                    f"Title: {option.title}",
                                    f"Address: {option.address}",
                                    f"Description: {option.description}",
                                    f"Services: {option.services}",
                                    f"Cost per person: {option.estimated_cost_per_person}",
                                ]
                            )
                        )
                        print()
                    return

                # Fallback: Some backends/versions may return a JSON string in `.text` even when `.value` is None.
                text = (getattr(response, "text", "") or "").strip()
                if text.startswith("{") and text.endswith("}"):
                    try:
                        venue_options = VenueOptionsModel.model_validate_json(text)
                    except Exception:
                        venue_options = None

                if venue_options:
                    print("Result: (parsed from response.text)")
                    for option in venue_options.options:
                        print(
                            "\n".join(
                                [
                                    f"Title: {option.title}",
                                    f"Address: {option.address}",
                                    f"Description: {option.description}",
                                    f"Services: {option.services}",
                                    f"Cost per person: {option.estimated_cost_per_person}",
                                ]
                            )
                        )
                        print()
                    return

                print("Result:")
                print("No structured data found in response.value")
                if text:
                    print("Raw text:")
                    print(text)


if __name__ == "__main__":
    try:
        if configure_otel_providers is not None:
            configure_otel_providers(exporters=[_DemoSpanExporter()])
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
