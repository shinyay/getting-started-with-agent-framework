# Agent Framework API Quick Reference

> **Based on `agent-framework-foundry>=1.2.2,<2.0`.**
> APIs may differ in other versions. When in doubt, check `requirements.txt` and the working code in `src/demo*.py`.

---

## Clients

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `FoundryChatClient(...)` | `credential` (async TokenCredential), `project_endpoint` (str, optional — falls back to `FOUNDRY_PROJECT_ENDPOINT` env), `model_deployment_name` (str, optional — falls back to `FOUNDRY_MODEL` env) | `FoundryChatClient` instance | `FoundryChatClient(credential=cred)` | demo1–6, event_planning entity |
| `OpenAIChatCompletionClient(...)` | `credential` (TokenCredential \| AzureKeyCredential), `endpoint` (str), `deployment_name` (str), `api_key` (str), `api_version` (str \| None) | `OpenAIChatCompletionClient` instance | `OpenAIChatCompletionClient(credential=cred, endpoint=ep, deployment_name=dep, api_key="", api_version=None)` | ai_genius entity |

**Import paths:**

```python
from agent_framework.foundry import FoundryChatClient
from agent_framework.openai import OpenAIChatCompletionClient
```

---

## Agent Creation

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `client.as_agent(...)` | `name` (str) — agent display name; `instructions` (str) — system prompt; `tools` (list[Tool], optional) — tool instances; `response_format` (type, optional) — Pydantic model for structured output | Async context manager → Agent | `client.as_agent(name="venue", instructions="...", tools=[...])` | All exercises |

**Usage patterns (both are valid):**

```python
# Pattern A: chained (demo1, demo2)
async with FoundryChatClient(credential=cred).as_agent(
    name="my_agent", instructions="..."
) as agent:
    ...

# Pattern B: separate client + agent (demo3, demo4, demo5)
async with FoundryChatClient(credential=cred) as client:
    async with client.as_agent(name="my_agent", instructions="...") as agent:
        ...

# Pattern C: factory function for DevUI entities (event_planning_workflow)
def create_my_agent():
    client = _get_client()
    return client.as_agent(name="my_agent", instructions="...")

# Pattern D: direct assignment without context manager (ai_genius_workflow)
agent = client.as_agent(name="Writer", instructions="...")
```

---

## Execution

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `agent.run(...)` | `prompt` (str) — user message; `response_format` (type \| None, optional) — Pydantic model | `ChatResponse` | `result = await agent.run("Plan a party")` | demo1–4 |
| `agent.run(... , response_format=Model)` | Same as above, with Pydantic model class | `ChatResponse` (`.value` populated with model instance) | `resp = await agent.run("Find venues", response_format=VenueOptionsModel)` | demo4 |
| `workflow.run_stream(...)` | `prompt` (str) — user message | `AsyncIterator` of streaming events | `async for event in workflow.run_stream("Plan a party"): ...` | demo5 |

---

## Response Types

| Type / Attribute | Type | Description | Used In |
|---|---|---|---|
| `ChatResponse` | class | Result from `agent.run()` | All exercises |
| `.text` | `str` | Plain-text response content | demo1–4 |
| `.value` | `BaseModel \| None` | Parsed Pydantic model when `response_format` is used | demo4 |
| `.messages` | `list` | Full conversation message list | demo5 (via event data) |

**Fallback pattern (demo4):** When `.value` is `None`, parse `.text` as JSON:

```python
venue_options = getattr(response, "value", None)
if not venue_options:
    text = (getattr(response, "text", "") or "").strip()
    if text.startswith("{"):
        venue_options = VenueOptionsModel.model_validate_json(text)
```

---

## Tools

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `client.get_web_search_tool(...)` | `description` (str, optional); `additional_properties` (dict, optional); `tool_properties` (dict, optional) | `client.get_web_search_tool` instance | See below | demo2, demo4, demo5, event_planning entity |
| `client.get_code_interpreter_tool(...)` | `description` (str, optional) | `client.get_code_interpreter_tool` instance | `client.get_code_interpreter_tool(description="Execute Python code...")` | demo5, event_planning entity |
| `MCPStdioTool(...)` | `name` (str), `command` (str), `args` (list[str]), `load_prompts` (bool) | `MCPStdioTool` instance | See below | demo3, demo5, event_planning entity |

**Import paths:**

```python
from agent_framework import client.get_web_search_tool
from agent_framework import client.get_code_interpreter_tool
from agent_framework import MCPStdioTool
```

### client.get_web_search_tool — `additional_properties` keys

| Key | Type | Description |
|---|---|---|
| `user_location` | `dict` (`{"city": str, "country": str}`) | Geo-hint for search results |
| `connection_id` | `str` | Foundry project connection ID for "Grounding with Bing Search" |
| `custom_connection_id` | `str` | Bing Custom Search connection ID |
| `custom_instance_name` | `str` | Bing Custom Search instance name |

**Usage — `additional_properties` style (demo2, demo4):**

```python
client.get_web_search_tool(
    additional_properties={
        "user_location": {"city": "Seattle", "country": "US"},
        "connection_id": bing_connection_id,
    }
)
```

**Usage — `tool_properties` style (demo5, event_planning entity):**

```python
client.get_web_search_tool(
    description="Search the web for current information using Bing",
    tool_properties={"connection_id": bing_connection_id},
)
```

### MCPStdioTool example

```python
MCPStdioTool(
    name="sequential-thinking",
    command="npx",
    load_prompts=False,
    args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
)
```

---

## Workflows

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `WorkflowBuilder(...)` | `name` (str, optional), `max_iterations` (int, optional) | `WorkflowBuilder` instance | `WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)` | demo5, event_planning entity, ai_genius entity |
| `.set_start_executor(agent_or_name)` _(removed in 1.2.2 — use `WorkflowBuilder(start_executor=...)` instead)_ | Agent instance or `str` (registered name) | `self` (chainable) | `.set_start_executor(coordinator)` _(removed in 1.2.2 — use `WorkflowBuilder(start_executor=...)` instead)_ | demo5, event_planning entity, ai_genius entity |
| `.add_edge(from, to)` | Agent instances or `str` (registered names) | `self` (chainable) | `.add_edge(coordinator, venue)` | demo5, event_planning entity, ai_genius entity |
| `.register_agent(factory_fn, name, output_response=False)` _(removed in 1.2.2 — materialize agents and pass instances directly to `.add_edge()`)_ | `factory_fn` (callable returning async context manager), `name` (str), `output_response` (bool) | `self` (chainable) | `.register_agent(create_booking_agent, "booking", output_response=True)` _(removed in 1.2.2 — materialize agents and pass instances directly to `.add_edge()`)_ | event_planning entity |
| `.build()` | — | `Workflow` | `.build()` | All workflow exercises |

**Two patterns for building workflows:**

```python
# Pattern A: Direct agent instances (demo5)
workflow = (
    WorkflowBuilder(name="...", max_iterations=30)
    # NOTE: 1.2.2 requires start_executor= passed to WorkflowBuilder() constructor
    .add_edge(coordinator, venue)
    .add_edge(venue, catering)
    .build()
)

# Pattern B: Registered agent factories (event_planning entity — DevUI compatible)
workflow = (
    WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
    # NOTE: 1.2.2 has no .register_agent() — pass agent instances to .add_edge() directly
    # NOTE: 1.2.2 — pass booking instance to output_executors=[booking] in WorkflowBuilder() constructor
    # NOTE: 1.2.2 — pass start_executor=coordinator instance to WorkflowBuilder() constructor
    .add_edge("coordinator", "venue")
    .build()
)

# Pattern C: Minimal (ai_genius entity)
workflow = (
    WorkflowBuilder(start_executor=writer, output_executors=[reviewer])
    .add_edge(writer, reviewer)
    .build()
)
```

---

## Events (Streaming)

| Type | Key Attributes | Description | Used In |
|---|---|---|---|
| `event.type == "data"` | `.executor_id` (str), `.data` (object) | Streamed update from an executor | demo5 |
| `event.type == "executor_completed"` | `.executor_id` (str), `.data` (object) | An executor finished; `.data` contains its output | demo5 |
| `event.type == "output"` | `.executor_id` (str), `.data` (object) | An executor yielded a final output | demo5 |

All workflow events are unified into a single `WorkflowEvent` class (Agent Framework 1.2.2); use `event.type` to discriminate.

**Import path:**

```python
from agent_framework import WorkflowEvent
```

**Streaming pattern (demo5):**

```python
async for event in workflow.run_stream(prompt):
    if event.type == "data":
        print(f"-> {event.executor_id}")
    elif event.type == "executor_completed":
        completed[event.executor_id] = event.data
    elif event.type == "output":
        final_output = event.data
```

---

## DevUI

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `serve(...)` | `entities` (list) — workflow/agent instances; `host` (str, default `"0.0.0.0"`); `port` (int, default `8080`); `auto_open` (bool) — open browser | `None` (blocks) | `serve(entities=[workflow], host="0.0.0.0", port=8080, auto_open=True)` | demo6 |

**Import path:**

```python
from agent_framework.devui import serve
```

---

## Credentials

| API / Method | Parameters | Returns | Notes | Used In |
|---|---|---|---|---|
| `azure.identity.aio.AzureCliCredential()` | — | Async credential (use with `async with`) | For `FoundryChatClient` (async context) | demo1–6, event_planning entity |
| `azure.identity.AzureCliCredential()` | — | Sync credential | For `OpenAIChatCompletionClient` (sync context) | ai_genius entity |
| `azure.core.credentials.AzureKeyCredential(key)` | `key` (str) | Key-based credential | For API key auth with Azure OpenAI | ai_genius entity (optional) |

---

## Observability

| API / Method | Parameters | Returns | Example | Used In |
|---|---|---|---|---|
| `configure_otel_providers(...)` | `exporters` (list[SpanExporter]) | `None` | `configure_otel_providers(exporters=[MyExporter()])` | demo1–5 |

**Import path:**

```python
from agent_framework.observability import configure_otel_providers
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
```

---

## Exceptions

| Type | Import Path | Notes | Used In |
|---|---|---|---|
| `ChatClientInvalidResponseException` | `agent_framework.exceptions` | Raised on Foundry API errors (model not found, 403, etc.) | demo2–5 |

---

## Environment Variables

| Name | Required By | Format | Example |
|---|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | demo1–6, event_planning entity | URL | `https://<account>.services.ai.azure.com/api/projects/<project-id>` |
| `FOUNDRY_MODEL` | demo1–6, event_planning entity | String | `gpt-4o` |
| `BING_CONNECTION_ID` | demo2, demo4, demo5, event_planning entity | Foundry connection ID string | `<guid-or-connection-name>` |
| `AZURE_OPENAI_ENDPOINT` | ai_genius entity | URL | `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | ai_genius entity | String | `gpt-4o` |
| `AZURE_OPENAI_API_KEY` | ai_genius entity (optional, API key auth) | String | `sk-...` |
| `AZURE_OPENAI_API_VERSION` | ai_genius entity (optional) | Date string | `2024-12-01-preview` |
| `AZURE_OPENAI_AUTH` | ai_genius entity (optional) | `api_key` or empty (Entra ID) | `api_key` |
| `DEVUI_HOST` | demo6 (optional) | IP / hostname | `0.0.0.0` |
| `DEVUI_PORT` | demo6 (optional) | Integer | `8080` |
| `DEMO_PAUSE` | demo5 (optional) | `1` / `true` / `yes` | `1` |
| `DEMO_NO_OPEN` | demo6 (optional) | `1` / `true` / `yes` | `1` |

### Bing connection alternative env var names

The exercise solutions accept both sets for convenience:

| Primary (Agent Framework runtime) | Alternative (Foundry docs) |
|---|---|
| `BING_CONNECTION_ID` | `BING_PROJECT_CONNECTION_ID` |
| `BING_CUSTOM_CONNECTION_ID` | `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID` |
| `BING_CUSTOM_INSTANCE_NAME` | `BING_CUSTOM_SEARCH_INSTANCE_NAME` |
