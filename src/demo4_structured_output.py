import asyncio
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from agent_framework.foundry import FoundryChatClient
from azure.ai.projects.models import (
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
)
from agent_framework.exceptions import ChatClientInvalidResponseException
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
            "If your Foundry project uses private networking / private DNS, run this demo from a network that can resolve the private endpoint, "
            "or switch to a public (non-private-link) project endpoint."
        ) from ex


def _build_bing_grounding_tool() -> dict:
    """Build a Foundry Bing Grounding tool dict from BING_CONNECTION_ID env var.

    Returns the dict serialization of `BingGroundingTool` so it can be passed
    directly through `client.as_agent(tools=[...])` to the Foundry Responses API.
    """
    connection_id = (os.getenv("BING_CONNECTION_ID") or os.getenv("BING_PROJECT_CONNECTION_ID") or "").strip()
    if not connection_id:
        raise RuntimeError(
            "Hosted Bing grounding requires BING_CONNECTION_ID (or BING_PROJECT_CONNECTION_ID).\n"
            "Set it to the full ARM resource ID of a Bing.Grounding connection in your Foundry project."
        )

    cfg = BingGroundingSearchConfiguration()
    cfg.project_connection_id = connection_id
    cfg.market = "en-US"
    cfg.count = 5
    return BingGroundingTool(
        bing_grounding=BingGroundingSearchToolParameters(search_configurations=[cfg])
    ).as_dict()


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
    # Validate the minimum required configuration for Microsoft Foundry Agents.
    project_endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    model = _require_env("FOUNDRY_MODEL")
    _check_project_endpoint_dns()
    bing_tool = _build_bing_grounding_tool()

    print("=" * 80)
    print("Demo 4: Structured Output (response_format) with Web Search")
    print("=" * 80)

    async with AzureCliCredential() as cred:
        print("Creating client...")
        client = FoundryChatClient(
            project_endpoint=project_endpoint,
            model=model,
            credential=cred,
        )
        print("Creating agent...")
        async with client.as_agent(
                name="venue_specialist",
                instructions=(
                    "You are the Venue Specialist, an expert in venue research and recommendation. "
                    "Use web search to find venue options and return only structured data that matches the provided schema."
                ),
                tools=[bing_tool],
            ) as agent:
                print("Running agent...")
                try:
                    response = await agent.run(
                        "Find venue options for a corporate holiday party for 50 people on December 6th, 2026 in Seattle",
                        options={"response_format": VenueOptionsModel},
                    )
                except ChatClientInvalidResponseException as ex:
                    msg = str(ex)
                    if "Failed to resolve model info" in msg:
                        raise RuntimeError(
                            "Microsoft Foundry could not resolve the model deployment specified by FOUNDRY_MODEL.\n\n"
                            "What to check:\n"
                            "- In the Foundry portal for this project, open 'Models + endpoints' and confirm the deployment name exists.\n"
                            "- FOUNDRY_MODEL must be the Foundry project model deployment name.\n\n"
                            "Current value:\n"
                            f"  FOUNDRY_MODEL={os.environ.get('FOUNDRY_MODEL','')}\n"
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
