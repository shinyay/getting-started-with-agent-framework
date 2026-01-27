import asyncio
import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import AgentResponse
from agent_framework.azure import AzureOpenAIChatClient
from dotenv import dotenv_values
from pydantic import BaseModel


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


def _check_endpoint_dns(url: str, env_name: str) -> None:
    host = urlparse(url).hostname
    if not host:
        raise RuntimeError(f"{env_name} does not look like a valid URL: {url}")
    try:
        socket.getaddrinfo(host, 443)
    except OSError as ex:
        raise RuntimeError(
            f"Cannot resolve {env_name} host via DNS from this environment.\n\n"
            f"  Host: {host}\n"
            f"  Value: {url}\n\n"
            "If your Azure OpenAI resource uses private networking / private DNS, run this demo from a network that can resolve it."
        ) from ex


class PersonInfo(BaseModel):
    """Information about a person."""

    name: str | None = None
    age: int | None = None
    occupation: str | None = None


def _make_agent():
    """Create a ChatAgent that supports structured output.

    By default we use Entra ID (Azure CLI) auth because some resources disable
    key-based auth.

    - Set AZURE_OPENAI_AUTH=api_key to force API key auth (no `az login` required).
    - Otherwise we use AzureCliCredential (requires `az login`).
    """

    endpoint = _require_env("AZURE_OPENAI_ENDPOINT")
    deployment = _require_env("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    api_version = (os.getenv("AZURE_OPENAI_API_VERSION") or "").strip() or None

    _check_endpoint_dns(endpoint, "AZURE_OPENAI_ENDPOINT")

    auth_mode = (os.getenv("AZURE_OPENAI_AUTH") or "").strip().lower()
    api_key = (os.getenv("AZURE_OPENAI_API_KEY") or "").strip()

    if auth_mode == "api_key":
        if not api_key:
            raise RuntimeError(
                "AZURE_OPENAI_AUTH=api_key is set but AZURE_OPENAI_API_KEY is empty."
            )
        # Import lazily so CLI-only users don't need this import path to resolve.
        from azure.core.credentials import AzureKeyCredential

        credential = AzureKeyCredential(api_key)
        client = AzureOpenAIChatClient(
            credential=credential,
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
        )
    else:
        from azure.identity import AzureCliCredential

        credential = AzureCliCredential()
        # Explicitly avoid key auth.
        client = AzureOpenAIChatClient(
            credential=credential,
            api_key="",
            endpoint=endpoint,
            deployment_name=deployment,
            api_version=api_version,
        )

    return client.as_agent(
        name="HelpfulAssistant",
        instructions=(
            "You are a helpful assistant that extracts person information from text. "
            "Return only the structured output that matches the provided schema."
        ),
    )


async def main() -> None:
    agent = _make_agent()

    query = "Please provide information about John Smith, who is a 35-year-old software engineer."

    print("=" * 80)
    print("Demo 4: Structured Output (response_format)")
    print("=" * 80)

    # 1) Non-streaming (easiest to understand)
    try:
        response = await agent.run(query, response_format=PersonInfo)
    except Exception as ex:
        msg = str(ex)
        if "403" in msg or "Forbidden" in msg:
            raise RuntimeError(
                "Request was forbidden. If your Azure OpenAI resource disables key-based auth, use Entra ID auth (default) and ensure you ran `az login` and have RBAC roles.\n\n"
                "Common fix: assign 'Cognitive Services OpenAI User' to your account on the Azure OpenAI resource.\n"
                "If you do want API key auth, set AZURE_OPENAI_AUTH=api_key and provide AZURE_OPENAI_API_KEY."
            ) from ex
        if "Credential" in msg and "not authenticated" in msg.lower():
            raise RuntimeError(
                "Azure CLI credential is not authenticated. Run `az login` and try again."
            ) from ex
        raise

    person = getattr(response, "value", None)
    if person:
        print("[non-stream]")
        print(f"  name       : {person.name}")
        print(f"  age        : {person.age}")
        print(f"  occupation : {person.occupation}")
    else:
        # Some backends/versions may return a JSON string in `.text` even when `.value` is None.
        # We keep the demo resilient by attempting to parse JSON into the expected Pydantic model.
        text = (getattr(response, "text", "") or "").strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                person = PersonInfo.model_validate_json(text)
            except Exception:
                person = None

        if person:
            print("[non-stream] (parsed from response.text)")
            print(f"  name       : {person.name}")
            print(f"  age        : {person.age}")
            print(f"  occupation : {person.occupation}")
        else:
            print("[non-stream] No structured data found in response.value")
            if text:
                print("Raw text:")
                print(text)

    # 2) Streaming (advanced)
    print("\n" + "-" * 80)
    print("[stream] collecting updates...")
    final_response = await AgentResponse.from_agent_response_generator(
        agent.run_stream(query, response_format=PersonInfo),
        output_format_type=PersonInfo,
    )

    person2 = getattr(final_response, "value", None)
    if person2:
        print("[stream]")
        print(f"  name       : {person2.name}")
        print(f"  age        : {person2.age}")
        print(f"  occupation : {person2.occupation}")
    else:
        print("[stream] No structured data found in final_response.value")
        text2 = (getattr(final_response, "text", "") or "").strip()
        if text2:
            print("Raw text:")
            print(text2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
