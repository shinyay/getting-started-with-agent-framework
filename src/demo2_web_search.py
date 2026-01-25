import asyncio
import os
from pathlib import Path

from agent_framework import HostedWebSearchTool
from agent_framework.azure import AzureAIAgentClient
from dotenv import load_dotenv
from azure.identity.aio import AzureCliCredential


# Load env vars from the repository root `.env`.
# NOTE: In Dev Containers, vars may be injected as empty strings via `containerEnv`.
#       We set override=True so `.env` can populate real values.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}. "
            "Set it via .env / export / Codespaces secrets and try again."
        )
    return value


async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")

    async with AzureCliCredential() as cred:
        # Azure AI Foundry Agents chat client (reads AZURE_AI_* from env by default)
        async with AzureAIAgentClient(credential=cred).as_agent(
            name="WebSearchAssistant",
            instructions="You are a helpful assistant with web search capabilities.",
            tools=[
                HostedWebSearchTool(
                    additional_properties={
                        "user_location": {"city": "Tokyo", "country": "JP"}
                    }
                )
            ],
        ) as agent:
            result = await agent.run("What are the latest news about AI?")
            print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
