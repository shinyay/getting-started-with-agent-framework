import asyncio
import os
from pathlib import Path

from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv


# Load env vars from the repository root `.env` (method 3 in demo1.md).
# `load_dotenv()` without an explicit path may not find it in some execution modes.
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
# NOTE: In Dev Containers, these vars may be injected as empty strings via
# `containerEnv`. We set override=True so `.env` can populate real values.
load_dotenv(dotenv_path=_DOTENV_PATH, override=True)


def _make_agent():
    """Create an Agent using either API key auth or Azure CLI auth.

    By default we use Entra ID (Azure CLI) auth because many Azure OpenAI
    resources have key-based auth disabled.

    - Set AZURE_OPENAI_AUTH=api_key to force API key auth (no `az login` required).
    - Otherwise we use AzureCliCredential (requires `az login`).
    """

    auth_mode = (os.getenv("AZURE_OPENAI_AUTH") or "").strip().lower()
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    if auth_mode == "api_key":
        if not api_key:
            raise RuntimeError(
                "AZURE_OPENAI_AUTH=api_key is set but AZURE_OPENAI_API_KEY is empty."
            )
        # Import lazily so CLI-only users don't need this import path to resolve.
        from azure.core.credentials import AzureKeyCredential

        credential = AzureKeyCredential(api_key)
        client = AzureOpenAIChatClient(credential=credential, api_key=api_key)
    else:
        from azure.identity import AzureCliCredential

        credential = AzureCliCredential()
        # Explicitly override any API key picked up from environment / .env.
        # Some resources disable key-based auth and require Entra ID.
        client = AzureOpenAIChatClient(credential=credential, api_key="")

    return client.as_agent(
        instructions="You are good at telling jokes.",
        name="Joker",
    )


agent = _make_agent()


async def main():
    result = await agent.run("Tell me a joke about a pirate.")
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
