import asyncio
import os
import shutil
import socket
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import (
    MCPStdioTool,
    WorkflowBuilder,
)
from agent_framework.foundry import FoundryChatClient
from azure.ai.projects.models import (
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
)
from agent_framework.exceptions import ChatClientInvalidResponseException
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values


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


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_result_item(item: object) -> None:
    # Many completion events wrap the payload in a single-item list.
    if isinstance(item, list):
        if len(item) == 1:
            item = item[0]
        else:
            for sub in item:
                _print_result_item(sub)
                print()
            return

    # Most common shape: an object with `.text`.
    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        print(text)
        return

    # Sometimes an executor completion wraps an agent response.
    agent_response = getattr(item, "agent_response", None)
    if agent_response is not None:
        # 1) Prefer plain text if available.
        text = getattr(agent_response, "text", None)
        if isinstance(text, str) and text.strip():
            print(text)
            return

        # 2) If structured output exists, print it (or recurse).
        value = getattr(agent_response, "value", None)
        if value is not None:
            _print_result_item(value)
            return

        # 3) Some responses carry messages even when `.text` is empty.
        messages = getattr(agent_response, "messages", None)
        if isinstance(messages, list) and messages:
            for m in reversed(messages):
                m_text = getattr(m, "text", None)
                if isinstance(m_text, str) and m_text.strip():
                    print(m_text)
                    return

        # 4) As a last attempt, print the last message in the full conversation.
        full_conversation = getattr(item, "full_conversation", None)
        if isinstance(full_conversation, list) and full_conversation:
            for m in reversed(full_conversation):
                m_text = getattr(m, "text", None)
                if isinstance(m_text, str) and m_text.strip():
                    print(m_text)
                    return

        # Fallback: print the wrapped response object rather than the full wrapper repr.
        print(agent_response)
        return

    # Fall back to printing the object itself.
    print(item)


def _require_command(cmd: str) -> str:
    resolved = shutil.which(cmd)
    if not resolved:
        raise RuntimeError(
            f"Required command is not available on PATH: {cmd}.\n\n"
            "Demo 5 uses a local MCP server launched via Node.js (npx).\n"
            "In this dev container, node/npx are typically preinstalled. "
            "If you're running elsewhere, install Node.js and try again."
        )
    return resolved


def _get_bing_tool_properties() -> dict:
    """Build Foundry web search tool configuration.

    We accept either the env var names referenced by the Agent Framework runtime
    or the names commonly used in Foundry docs.
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



def _build_bing_grounding_tool() -> dict:
    """Build Foundry Bing Grounding tool dict from BING_CONNECTION_ID env var."""
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

async def _create_agent_factory() -> tuple[FoundryChatClient, callable, callable]:
    """Return (client, agent_factory, close).

    The client is returned so callers can use `client.get_web_search_tool(...)` and
    `client.get_code_interpreter_tool(...)` factory methods to build hosted tools.
    The agent instances returned by agent_factory are entered into an AsyncExitStack
    so they are cleaned up reliably.
    """

    project_endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    model = _require_env("FOUNDRY_MODEL")

    stack = AsyncExitStack()
    cred = await stack.enter_async_context(AzureCliCredential())

    # FoundryChatClient is NOT an async context manager in 1.2.2; just instantiate it.
    # The async cleanup happens when the credential leaves its async with block.
    client = FoundryChatClient(
        project_endpoint=project_endpoint,
        model=model,
        credential=cred,
    )

    async def agent_factory(**kwargs):
        return await stack.enter_async_context(client.as_agent(**kwargs))

    async def close() -> None:
        await stack.aclose()

    return client, agent_factory, close


async def main() -> None:
    # Validate the minimum required configuration for Microsoft Foundry Agents.
    _require_env("FOUNDRY_PROJECT_ENDPOINT")
    _require_env("FOUNDRY_MODEL")
    _check_project_endpoint_dns()

    # Demo 5 uses an MCP server started via npx.
    _require_command("npx")

    # Demo 5 also uses Hosted Web Search (Bing grounding).
    # Bing grounding will be wired via _build_bing_grounding_tool() in agent factory closures

    client, agent, close = await _create_agent_factory()
    try:
        coordinator = await agent(
            name="coordinator",
            instructions=(
                "You are the Event Coordinator. You orchestrate a team of specialists to plan an event. "
                "First, create a clear step-by-step plan for what each specialist must deliver, then proceed through the workflow. "
                "Use the sequential-thinking tool to plan before answering."
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

        venue = await agent(
            name="venue",
            instructions=(
                "You are the Venue Specialist. Recommend venues for the event and justify your choices. "
                "Consider capacity, location, accessibility, amenities, and vibe."
            ),
            tools=[
                _build_bing_grounding_tool(),
            ],
        )

        catering = await agent(
            name="catering",
            instructions=(
                "You are the Catering Coordinator. Propose food & beverage options for the event. "
                "Include options for common dietary restrictions by default, and match the plan to the venue and schedule."
            ),
            tools=[
                _build_bing_grounding_tool(),
            ],
        )

        budget_analyst = await agent(
            name="budget_analyst",
            instructions=(
                "You are the Budget Analyst. Create a reasonable per-person estimate and allocate costs across venue, catering, AV, staffing, and contingency. "
                "When you need calculations, use the code interpreter tool."
            ),
            tools=[
                client.get_code_interpreter_tool().as_dict(),
            ],
        )

        booking = await agent(
            name="booking",
            instructions=(
                "You are the Event Booking Specialist. Synthesize all prior specialist outputs into one cohesive event plan. "
                "Use markdown headings and bullet points. Include an executive summary, venue, catering, budget, logistics, and next steps."
            ),
        )

        # Coordinator -> Venue -> Catering -> Budget -> Booking
        # Agent Framework 1.2.2 requires `start_executor` and `output_executors` at builder construction.
        workflow = (
            WorkflowBuilder(
                name="Event Planning Workflow",
                max_iterations=30,
                start_executor=coordinator,
                output_executors=[booking],
            )
            .add_edge(coordinator, venue)
            .add_edge(venue, catering)
            .add_edge(catering, budget_analyst)
            .add_edge(budget_analyst, booking)
            .build()
        )

        _print_header(
            "Demo 5: Multi-agent workflow (coordinator -> venue -> catering -> budget_analyst -> booking)"
        )

        prompt = "Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
        print("Running workflow...\n")

        chain = ["coordinator", "venue", "catering", "budget_analyst", "booking"]
        completed: dict[str, object] = {}
        final_output: object | None = None

        try:
            events = workflow.run(prompt, stream=True)
            last_executor_id: str | None = None
            async for event in events:
                # In Agent Framework 1.2.2, all workflow events are unified into a
                # single WorkflowEvent class with a `type` discriminator.
                if event.type == "data":
                    # Show which executor is currently producing updates (no token spam).
                    if event.executor_id != last_executor_id:
                        print(f"-> {event.executor_id}")
                        last_executor_id = event.executor_id
                elif event.type == "executor_completed":
                    if event.data is not None and event.executor_id is not None:
                        completed[event.executor_id] = event.data
                elif event.type == "output":
                    final_output = event.data
        except ChatClientInvalidResponseException as ex:
            msg = str(ex)
            if "Failed to resolve model info" in msg:
                raise RuntimeError(
                    "Microsoft Foundry could not resolve the model deployment specified by FOUNDRY_MODEL.\n\n"
                    "What to check:\n"
                    "- In the Foundry portal for this project, open 'Models + endpoints' and confirm the deployment name exists.\n"
                    "- FOUNDRY_MODEL must be the Foundry project model deployment name (it is often NOT the same as your Azure OpenAI deployment name used in Demo 1).\n\n"
                    "Current value:\n"
                    f"  FOUNDRY_MODEL={os.environ.get('FOUNDRY_MODEL','')}\n"
                ) from ex

            # Common auth errors (RBAC / not logged in)
            if "403" in msg or "Forbidden" in msg:
                raise RuntimeError(
                    "Request was forbidden (403).\n\n"
                    "What to check:\n"
                    "- You ran `az login` (this demo uses AzureCliCredential).\n"
                    "- Your Entra ID has RBAC permissions for the Foundry project/hub.\n"
                    "  (Ask an admin to grant the appropriate role for running Agents.)\n"
                ) from ex
            if "Credential" in msg and "not authenticated" in msg.lower():
                raise RuntimeError(
                    "Azure CLI credential is not authenticated. Run `az login` and try again."
                ) from ex
            raise

        print("\nWorkflow Result:\n")

        # Prefer per-executor completion payloads (most reliable for this pinned SDK).
        printed_any = False
        for executor_id in chain:
            if executor_id not in completed:
                continue
            printed_any = True
            print(f"### {executor_id}")
            _print_result_item(completed[executor_id])
            print()

        # If we didn't capture per-executor completions, fall back to final output.
        if not printed_any and final_output is not None:
            _print_result_item(final_output)

        # Optional pause for live demos; keep it opt-in to avoid blocking automation.
        if os.getenv("DEMO_PAUSE", "").strip().lower() in {"1", "true", "yes"} and sys.stdin.isatty():
            input("Press Enter to exit...")

    finally:
        await close()


if __name__ == "__main__":
    if configure_otel_providers is not None:
        configure_otel_providers(exporters=[_DemoSpanExporter()])
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
