"""Demo 7: Foundry Toolboxes + Hosted Agent V2 (1.2.2 features).

This demo showcases two new capabilities introduced in Microsoft Agent Framework 1.2.2:

1. **Foundry Toolboxes** — group multiple tools (including hosted tools and MCP servers)
   under one logical name in the Foundry portal, then attach the entire toolbox to your
   agent with a single reference. Use `select_toolbox_tools()` to load a toolbox by name
   and optionally filter which tools inside it become available to this agent run.

2. **Hosted Agent V2** — connect to a service-managed agent that already exists in your
   Foundry project (created via the Foundry portal, AZD CLI, or VS Code Foundry Toolkit).
   You bring `agent_name` (and optionally `agent_version`); Foundry brings the runtime,
   identity, tools, and tracing.

This demo is **best-effort**: it does NOT create a Toolbox or Hosted Agent for you (the
Foundry CRUD APIs for those are still preview surfaces). It demonstrates how to *consume*
them once they exist. If neither is configured in your project, the demo prints clear
fix-up instructions and exits.

Required environment variables:
    FOUNDRY_PROJECT_ENDPOINT    — your Foundry project endpoint
    FOUNDRY_MODEL               — model deployment name (used as fallback for the inline agent)
    FOUNDRY_TOOLBOX_NAME        — (optional) name of an existing Foundry Toolbox to consume
    FOUNDRY_AGENT_NAME          — (optional) name of an existing Hosted Agent to invoke

Run:
    python3 -u src/demo7_toolbox.py
"""

import asyncio
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from agent_framework.foundry import FoundryAgent, FoundryChatClient, select_toolbox_tools
from agent_framework.exceptions import AgentFrameworkException, ChatClientInvalidResponseException
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values


# Load env vars from the repository root `.env` (fill-only).
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
            f"FOUNDRY_PROJECT_ENDPOINT is not a valid URL: {endpoint}"
        )
    try:
        socket.getaddrinfo(host, 443)
    except OSError as ex:
        raise RuntimeError(
            f"Cannot resolve {host} via DNS. If your Foundry project uses private "
            "networking, run this demo from a network with private DNS resolution."
        ) from ex


async def demo_toolbox_consumer() -> None:
    """Demonstrate consuming a Foundry Toolbox.

    Pre-requisite: a Toolbox named ${FOUNDRY_TOOLBOX_NAME} exists in your Foundry project,
    grouping (e.g.) a Bing web search and a code interpreter.
    """
    toolbox_name = (os.getenv("FOUNDRY_TOOLBOX_NAME") or "").strip()
    if not toolbox_name:
        print(
            "[Toolbox demo] Skipped — FOUNDRY_TOOLBOX_NAME not set.\n"
            "  To enable: create a Toolbox in the Foundry portal, then set\n"
            "  FOUNDRY_TOOLBOX_NAME=<your-toolbox-name> in .env and re-run."
        )
        return

    project_endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    model = _require_env("FOUNDRY_MODEL")

    async with AzureCliCredential() as cred:
        client = FoundryChatClient(
            project_endpoint=project_endpoint,
            model=model,
            credential=cred,
        )
        try:
            # `select_toolbox_tools` accepts a list-of-tools (or dicts) and filters by
            # name / type / predicate. Here we ask for the entire toolbox by name and
            # only keep web_search + code_interpreter tools from it.
            toolbox_tools = select_toolbox_tools(
                tools=toolbox_name,
                include_types=["web_search", "code_interpreter"],
            )
            async with client.as_agent(
                name="toolbox_consumer",
                instructions=(
                    "You are a research assistant. Use the tools attached from the Foundry Toolbox "
                    "to answer the user's question; show the calculation when relevant."
                ),
                tools=toolbox_tools,
            ) as agent:
                print(f"[Toolbox demo] Using Toolbox: {toolbox_name}")
                print(f"[Toolbox demo] Tools loaded: {len(toolbox_tools)}")
                result = await agent.run(
                    "What is the average daily temperature of Seattle in December? "
                    "Use the web search tool, then estimate the heating cost for an "
                    "8-hour event with the code interpreter (assume 5 kW heater + $0.12/kWh)."
                )
                print(result.text)
        except (AgentFrameworkException, ChatClientInvalidResponseException) as ex:
            print(
                f"[Toolbox demo] Failed: {ex}\n"
                "  Common causes:\n"
                f"  - Toolbox '{toolbox_name}' does not exist in this Foundry project.\n"
                "  - The included tool types are not present in the toolbox.\n"
                "  - Microsoft.CognitiveServices/FoundryComputePreview not registered.\n"
            )


async def demo_hosted_agent_consumer() -> None:
    """Demonstrate connecting to an existing Hosted Agent V2."""
    agent_name = (os.getenv("FOUNDRY_AGENT_NAME") or "").strip()
    if not agent_name:
        print(
            "[Hosted Agent demo] Skipped — FOUNDRY_AGENT_NAME not set.\n"
            "  To enable: create a Hosted Agent in the Foundry portal (or via AZD CLI),\n"
            "  then set FOUNDRY_AGENT_NAME=<your-agent-name> (and optionally\n"
            "  FOUNDRY_AGENT_VERSION) in .env and re-run."
        )
        return

    project_endpoint = _require_env("FOUNDRY_PROJECT_ENDPOINT")
    agent_version = (os.getenv("FOUNDRY_AGENT_VERSION") or "").strip() or None

    async with AzureCliCredential() as cred:
        try:
            async with FoundryAgent(
                project_endpoint=project_endpoint,
                agent_name=agent_name,
                agent_version=agent_version,
                credential=cred,
            ) as agent:
                print(f"[Hosted Agent demo] Connected to Hosted Agent: {agent_name}")
                if agent_version:
                    print(f"[Hosted Agent demo] Version: {agent_version}")
                result = await agent.run(
                    "Hello! Please tell me what you do and which tools you have available."
                )
                print(result.text)
        except (AgentFrameworkException, ChatClientInvalidResponseException) as ex:
            print(
                f"[Hosted Agent demo] Failed: {ex}\n"
                "  Common causes:\n"
                f"  - Hosted Agent '{agent_name}' does not exist in this Foundry project.\n"
                "  - Microsoft.CognitiveServices/FoundryComputePreview not registered.\n"
                "    Fix:  az feature register --namespace Microsoft.CognitiveServices "
                "--name FoundryComputePreview\n"
                "          az provider register -n Microsoft.CognitiveServices\n"
            )


async def main() -> None:
    _require_env("FOUNDRY_PROJECT_ENDPOINT")
    _require_env("FOUNDRY_MODEL")
    _check_project_endpoint_dns()

    print("=" * 80)
    print("Demo 7: Foundry Toolboxes + Hosted Agent V2 (Agent Framework 1.2.2)")
    print("=" * 80)
    print()

    print(">> Part 1: Consume a Foundry Toolbox")
    print("-" * 80)
    await demo_toolbox_consumer()
    print()

    print(">> Part 2: Connect to a Hosted Agent")
    print("-" * 80)
    await demo_hosted_agent_consumer()


if __name__ == "__main__":
    asyncio.run(main())
