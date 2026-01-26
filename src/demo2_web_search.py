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
    """Fail fast if the Foundry project endpoint hostname cannot be resolved.

    This commonly happens when:
    - the endpoint value is mistyped, or
    - the Foundry account/project is configured with private networking and
      requires private DNS that is not available in the current environment.
    """

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


async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()
    bing_props = _get_bing_tool_properties()

    async with AzureCliCredential() as cred:
        # Azure AI Foundry Agents chat client (reads AZURE_AI_* from env by default)
        async with AzureAIAgentClient(credential=cred).as_agent(
            name="WebSearchAssistant",
            instructions="You are a helpful assistant with web search capabilities.",
            tools=[
                HostedWebSearchTool(
                    additional_properties={
                        "user_location": {"city": "Tokyo", "country": "JP"},
                        **bing_props,
                    }
                )
            ],
        ) as agent:
            try:
                result = await agent.run("What are the latest news about AI?")
            except ServiceResponseException as ex:
                msg = str(ex)
                if "Failed to resolve model info" in msg:
                    raise RuntimeError(
                        "Azure AI Foundry could not resolve the model deployment specified by AZURE_AI_MODEL_DEPLOYMENT_NAME.\n\n"
                        "What to check:\n"
                        "- In the Foundry portal for this project, open 'Models + endpoints' and confirm the deployment name exists.\n"
                        "- AZURE_AI_MODEL_DEPLOYMENT_NAME must be the Foundry project model deployment name (it is often NOT the same as your Azure OpenAI deployment name used in Demo 1).\n\n"
                        "Current value:\n"
                        f"  AZURE_AI_MODEL_DEPLOYMENT_NAME={os.environ.get('AZURE_AI_MODEL_DEPLOYMENT_NAME','')}\n"
                    ) from ex
                raise

            print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
