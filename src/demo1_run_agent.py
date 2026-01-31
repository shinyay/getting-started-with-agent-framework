import asyncio
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

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


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers / Codespaces, vars may be injected as empty strings.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"

# We do NOT blindly override: it's useful to temporarily override values via
# `VAR=... python ...` when debugging.
# Instead, we fill only missing/empty environment variables from `.env`.
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


class _DemoSpanExporter(SpanExporter):
    """Print one concise line per span (agent runs + tool calls).

    This keeps the demo output readable while still showing when agents/tools run.
    It's optional (only enabled if OpenTelemetry is available).
    """

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

    async with AzureCliCredential() as cred:
        async with AzureAIAgentClient(credential=cred).as_agent(
            name="venue_specialist",
            instructions="You are the Venue Specialist, an expert in venue research and recommendation.",
        ) as agent:
            result = await agent.run(
                "Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
            )
            print("Result:\n")
            print(result.text)


if __name__ == "__main__":
    if configure_otel_providers is not None:
        configure_otel_providers(exporters=[_DemoSpanExporter()])
    asyncio.run(main())
