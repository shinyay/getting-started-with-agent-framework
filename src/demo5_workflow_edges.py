import asyncio
import os
import socket
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import urlparse

from agent_framework import (
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
    WorkflowBuilder,
    WorkflowOutputEvent,
)
from agent_framework.azure import AzureAIAgentClient
from agent_framework.exceptions import ServiceResponseException
from azure.identity.aio import AzureCliCredential
from dotenv import dotenv_values


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


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


async def _create_agent_factory() -> tuple[callable, callable]:
    """Return (agent_factory, close).

    The agent instances returned by agent_factory are entered into an AsyncExitStack
    so they are cleaned up reliably.
    """

    stack = AsyncExitStack()
    cred = await stack.enter_async_context(AzureCliCredential())

    # Keep a single client alive for the duration of the run.
    client = await stack.enter_async_context(AzureAIAgentClient(credential=cred))

    async def agent_factory(**kwargs):
        return await stack.enter_async_context(client.as_agent(**kwargs))

    async def close() -> None:
        await stack.aclose()

    return agent_factory, close


async def main() -> None:
    # Validate the minimum required configuration for Azure AI Foundry Agents.
    _require_env("AZURE_AI_PROJECT_ENDPOINT")
    _require_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    _check_project_endpoint_dns()

    agent, close = await _create_agent_factory()
    try:
        writer = await agent(
            name="Writer",
            instructions=(
                "You are an excellent content writer. "
                "You create new content and edit content based on feedback."
            ),
        )
        reviewer = await agent(
            name="Reviewer",
            instructions=(
                "You are an excellent content reviewer. "
                "Provide actionable feedback to the writer about the provided content. "
                "Provide the feedback in the most concise manner possible."
            ),
        )

        workflow = (
            WorkflowBuilder()
            .set_start_executor(writer)
            .add_edge(writer, reviewer)
            .build()
        )

        _print_header("Demo 5: Workflow with edges (Writer -> Reviewer)")

        last_executor_id: str | None = None
        output_printed = False
        last_completed: dict[str, object] = {}
        prompt = "Create a slogan for a new electric SUV that is affordable and fun to drive."
        events = workflow.run_stream(prompt)

        try:
            async for event in events:
                if isinstance(event, AgentRunUpdateEvent):
                    eid = event.executor_id
                    if eid != last_executor_id:
                        if last_executor_id is not None:
                            print()
                        print(f"{eid}:", end=" ", flush=True)
                        last_executor_id = eid

                    update = event.data
                    chunk = getattr(update, "text", None)
                    if chunk is None:
                        # Best-effort fallback for versions/backends that send token deltas in a different field.
                        chunk = str(update)
                    print(chunk, end="", flush=True)

                elif isinstance(event, WorkflowOutputEvent):
                    print("\n===== Final output =====")
                    print(event.data)
                    output_printed = True

                elif isinstance(event, ExecutorCompletedEvent):
                    # In some pinned versions, the final output is surfaced via completion events.
                    # We'll keep the most recent completion payload per executor.
                    if event.data is not None:
                        last_completed[event.executor_id] = event.data
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

        if not output_printed:
            # Best-effort final output (usually the last executor is the reviewer).
            candidate = None
            if "Reviewer" in last_completed:
                candidate = last_completed["Reviewer"]
            elif last_completed:
                candidate = next(reversed(last_completed.values()))

            if candidate is not None:
                # Some executors return a list of responses.
                if isinstance(candidate, list) and len(candidate) == 1:
                    candidate = candidate[0]

                # ExecutorCompletedEvent often carries an AgentExecutorResponse wrapper.
                agent_response = getattr(candidate, "agent_response", None)
                if agent_response is not None:
                    candidate = agent_response

                text = getattr(candidate, "text", None)
                print("\n===== Final output (best-effort) =====")
                print(text if isinstance(text, str) and text.strip() else candidate)

    finally:
        await close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
