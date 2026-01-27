import asyncio
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import HostedMCPTool, HostedWebSearchTool
from agent_framework.exceptions import ServiceResponseException
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers, vars may be injected as empty strings via `containerEnv`.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"

# We *do not* blindly override, because it's useful to be able to temporarily
# override values via `VAR=... python ...` when debugging.
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


def _get_bing_tool_properties() -> dict:
    """Build HostedWebSearchTool configuration.

    Demo 3 mixes Microsoft Learn MCP with hosted web search so we can observe
    sequential tool calls. Hosted web search requires a Bing connection.

    We accept both the env var names referenced by the library and those used in docs.
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
        "This demo uses HostedWebSearchTool (for sequential tool calls), which requires a Bing connection. Set either:\n"
        "  - BING_CONNECTION_ID (or BING_PROJECT_CONNECTION_ID)\n"
        "  - OR BING_CUSTOM_CONNECTION_ID + BING_CUSTOM_INSTANCE_NAME\n"
        "    (or BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID + BING_CUSTOM_SEARCH_INSTANCE_NAME)\n\n"
        "If you want to run MCP-only, remove HostedWebSearchTool from the script and prompt."
    )


MSLEARN_MCP_URL = "https://learn.microsoft.com/api/mcp"


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def _run_with_mcp_and_websearch(cred: AzureCliCredential) -> tuple[bool, str]:
    """Try Demo 3 as intended: MCP first, then Web Search.

    Returns (ok, text). If ok is False, text may be empty.
    """

    bing_props = _get_bing_tool_properties()

    async with AzureAIAgentClient(credential=cred).as_agent(
        name="DocAssistant",
        instructions=(
            "You are a documentation assistant. Prefer official docs and cite the source section titles you used. "
            "Use Microsoft Learn MCP first for authoritative steps, then use Web Search to confirm any recent UI changes."
        ),
        tools=[
            HostedMCPTool(
                name="Microsoft Learn MCP",
                url=MSLEARN_MCP_URL,
            ),
            HostedWebSearchTool(
                additional_properties={
                    "user_location": {"city": "Tokyo", "country": "JP"},
                    **bing_props,
                }
            ),
        ],
    ) as agent:
        prompt = (
            "I want to create an Azure Storage account.\n"
            "1) Use Microsoft Learn MCP to find the official steps.\n"
            "2) Then use Web Search to confirm any recent UI changes.\n"
            "3) Output: numbered steps + a short Azure CLI example.\n"
            "4) If a tool fails or returns nothing, say so and continue with best-effort guidance.\n"
        )

        try:
            result = await agent.run(prompt)
        except ServiceResponseException as ex:
            if os.getenv("DEMO3_DEBUG") == "1":
                print(f"[debug] ServiceResponseException: {ex}", file=sys.stderr)
            return False, ""

        text = (getattr(result, "text", "") or "").strip()
        return bool(text), text


async def _run_with_websearch_only(cred: AzureCliCredential) -> str:
    """Fallback when MCP tool isn't available/unstable in the current backend."""

    bing_props = _get_bing_tool_properties()

    async with AzureAIAgentClient(credential=cred).as_agent(
        name="DocAssistant-WebSearchFallback",
        instructions=(
            "You are a documentation assistant. Use web search results to locate official Microsoft Learn documentation and summarize it. "
            "Prefer official docs and include links when possible."
        ),
        tools=[
            HostedWebSearchTool(
                additional_properties={
                    "user_location": {"city": "Tokyo", "country": "JP"},
                    **bing_props,
                }
            )
        ],
    ) as agent:
        prompt = (
            "Find the official Microsoft documentation for creating an Azure Storage account and summarize the steps. "
            "Output: numbered steps + a short Azure CLI example."
        )
        result = await agent.run(prompt)
        return (getattr(result, "text", "") or "").strip()


async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()

    async with AzureCliCredential() as cred:
        _print_header("Demo 3: Microsoft Learn MCP + Hosted Web Search")

        try:
            ok, text = await _run_with_mcp_and_websearch(cred)
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

        if ok:
            print(text)
            return

        print(
            "(Note) Microsoft Learn MCP tool call did not produce a usable response in this environment. "
            "Falling back to Hosted Web Search only.\n"
        )

        _print_header("Demo 3 (fallback): Hosted Web Search only")
        fallback_text = await _run_with_websearch_only(cred)
        print(fallback_text)



if __name__ == "__main__":
    asyncio.run(main())
