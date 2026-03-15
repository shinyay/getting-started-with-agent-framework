# Microsoft Agent Framework — Supplementary Workshop Guide

> **Pinned version in this repository:** `agent-framework==1.0.0b260123`
>
> Official Microsoft Learn documentation may reference the **latest** pre-release. APIs, parameter names, and event shapes can differ between versions. **When in doubt, trust the code in this repository** and the version pinned in `requirements.txt`.

---

## 1. What is Microsoft Agent Framework?

Microsoft Agent Framework is an open-source SDK — available for both **.NET** and **Python** — that provides a unified, code-first programming model for building AI Agents and multi-agent Workflows. It merges concepts that previously lived in two separate Microsoft projects (Semantic Kernel and AutoGen) into a single coherent surface.

The framework rests on **two pillars**:

| Pillar | Purpose |
|---|---|
| **AI Agents** | A single agent that combines an LLM with instructions and tools to complete a task autonomously. |
| **Workflows** | A graph of agents connected by edges that execute in sequence (or conditionally), producing a composite result. |

Key design principles:

- **Code-first** — agents, tools, and workflows are defined in Python (or C#), not YAML or a drag-and-drop UI.
- **Cloud-backed** — the SDK sends requests to Azure AI Foundry, which hosts the LLM, tool orchestration, and (optionally) hosted tools such as Bing Web Search and a sandboxed code interpreter.
- **Async-native** — the Python surface is built on `asyncio`; all I/O operations (`run()`, `run_stream()`, credential management) are async.

> **Reference:** [Agent Framework Overview — Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview/)

---

## 2. Architecture Overview

### Client Types

The framework ships two primary client classes. This workshop uses only the first:

| Client | Backend | Import |
|---|---|---|
| `AzureAIAgentClient` | Azure AI Foundry (Agents API) | `from agent_framework.azure import AzureAIAgentClient` |
| `AzureOpenAIChatClient` | Azure OpenAI (Chat Completions API) | `from agent_framework.azure import AzureOpenAIChatClient` |

`AzureAIAgentClient` is the richer option: it supports hosted tools (Bing Search, Code Interpreter) and the Foundry Agents runtime. `AzureOpenAIChatClient` talks directly to an Azure OpenAI deployment and is useful when you only need basic chat completions with custom function tools.

### Agent Lifecycle

Every demo in this workshop follows the same lifecycle:

```
create credential → create client → as_agent() → run() / run_stream() → close
```

Concretely (from `src/demo1_run_agent.py`):

```python
async with AzureCliCredential() as cred:
    async with AzureAIAgentClient(credential=cred).as_agent(
        name="venue_specialist",
        instructions="You are the Venue Specialist, an expert in venue research ...",
    ) as agent:
        result = await agent.run("Plan a corporate holiday party ...")
        print(result.text)
```

Each `async with` block guarantees resource cleanup. The credential, the client, and the agent are all async context managers.

### Credential Model

| Method | When to use |
|---|---|
| **Entra ID — `AzureCliCredential`** | Development / workshop (requires `az login`) |
| **Entra ID — `DefaultAzureCredential`** | Production (supports managed identity, workload identity, etc.) |
| **API key** | Quick experiments (not recommended for shared environments) |

This workshop uses `AzureCliCredential` from `azure.identity.aio` — note the `.aio` sub-package for the async variant.

### How It Works (Simplified)

```
┌──────────┐       ┌─────────────────────┐       ┌──────────────────────┐
│          │       │                     │       │  Azure AI Foundry    │
│  Your    │──────▶│  Agent Framework    │──────▶│  ┌────────────────┐  │
│  Code    │       │  SDK (Python)       │       │  │ LLM Deployment │  │
│          │◀──────│                     │◀──────│  └────────────────┘  │
└──────────┘       └─────────────────────┘       │  ┌────────────────┐  │
                                                 │  │ Hosted Tools   │  │
                                                 │  │ (Bing, Code    │  │
                                                 │  │  Interpreter)  │  │
                                                 │  └────────────────┘  │
                                                 └──────────────────────┘
```

Your code never calls the LLM directly. The SDK sends the prompt, instructions, and tool definitions to Foundry's Agents runtime, which orchestrates the LLM invocation(s) and tool calls, then returns a consolidated response.

---

## 3. Core Concepts: Agents

An Agent in this framework is the combination of three things:

1. **An LLM** — the model deployment specified by `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
2. **Instructions** — a system-level prompt that defines the agent's persona and behavior.
3. **Tools** — optional capabilities the agent can invoke (web search, code execution, MCP servers, custom functions).

### `as_agent()` Parameters

| Parameter | Type | Purpose |
|---|---|---|
| `name` | `str` | Human-readable identifier (appears in OTel spans, DevUI, logs) |
| `instructions` | `str` | System prompt that guides the agent's behavior |
| `tools` | `list` | Tool instances (`HostedWebSearchTool`, `MCPStdioTool`, etc.) |
| `response_format` | `type[BaseModel]` | Pydantic model class for structured output (see §5) |

### `run()` — Single-Turn Execution

`run()` sends a user message, waits for the agent to complete (including any tool calls the LLM decides to make), and returns a `ChatResponse`:

```python
result = await agent.run("Find venue options in Seattle")
print(result.text)       # The agent's text reply
print(result.value)      # Typed Pydantic object (if response_format was set)
print(result.messages)   # Full conversation history
```

### `run_stream()` — Streaming Execution

`run_stream()` returns an async iterator of events, allowing real-time UI updates as the agent works. This is what the workflow demos use (see §6).

### Async Resource Management

Both `AzureCliCredential` and `AzureAIAgentClient` hold network connections. Always use `async with` to ensure they are closed:

```python
async with AzureCliCredential() as cred:
    async with AzureAIAgentClient(credential=cred) as client:
        async with client.as_agent(...) as agent:
            ...
```

When managing multiple agents (as in `src/demo5_workflow_edges.py`), use `contextlib.AsyncExitStack` to register each agent and clean up in a single `finally` block.

---

## 4. Core Concepts: Tools

### 4a. Hosted Tools (Run on the Foundry Backend)

Hosted tools execute **server-side** inside Azure AI Foundry. Your local machine never runs the tool logic — Foundry does.

#### `HostedWebSearchTool`

Provides Bing-grounded web search. The agent can autonomously decide to search the web when the prompt requires current information.

```python
from agent_framework import HostedWebSearchTool

HostedWebSearchTool(
    additional_properties={
        "user_location": {"city": "Seattle", "country": "US"},
        "connection_id": "<your-bing-connection-id>",
    }
)
```

Key configuration in `additional_properties`:

| Property | Purpose |
|---|---|
| `connection_id` | Project connection ID for "Grounding with Bing Search" |
| `custom_connection_id` + `custom_instance_name` | For Bing Custom Search instances |
| `user_location` | Hint for location-aware results (city, country) |

The connection must be created in the Azure AI Foundry portal under your project's **Connected resources**. This is **not** a raw Bing API key — it is a Foundry-managed connection.

An alternative form used in the workflow entity (`entities/event_planning_workflow/workflow.py`) passes `tool_properties` and `description` instead:

```python
HostedWebSearchTool(
    description="Search the web for current information using Bing",
    tool_properties={"connection_id": "..."},
)
```

Both forms are valid in the pinned SDK version.

#### `HostedCodeInterpreterTool`

Provides a sandboxed Python runtime on Foundry for calculations and data analysis:

```python
from agent_framework import HostedCodeInterpreterTool

HostedCodeInterpreterTool(
    description="Execute Python code for calculations: budget breakdowns, totals, per-person estimates."
)
```

The `description` parameter is important — it tells the LLM **when** to use this tool. Without it, the agent may not recognize that a code sandbox is available.

### 4b. MCP Tools (Local Process)

#### `MCPStdioTool`

Launches a local MCP server as a child process and communicates via `stdio` transport:

```python
from agent_framework import MCPStdioTool

MCPStdioTool(
    name="sequential-thinking",
    command="npx",
    load_prompts=False,
    args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
)
```

| Parameter | Purpose |
|---|---|
| `name` | Identifier for the MCP server (used in logs and OTel spans) |
| `command` | The executable to spawn (e.g., `npx`, `python`, `node`) |
| `args` | Command-line arguments passed to the process |
| `load_prompts` | Whether to load prompt templates from the MCP server (set `False` if not needed) |

**Security note:** The child process runs with your local user's permissions. Only use MCP servers you trust. The `_require_command()` pattern in the demos validates that the required executable (`npx`) is available before attempting to create the tool.

### 4c. Custom Function Tools

You can register plain Python functions as agent tools. The framework uses type hints and docstrings to generate the tool schema that the LLM sees. This workshop does not demonstrate custom function tools directly, but the capability exists for cases where you need arbitrary local logic.

### 4d. How Agents Decide to Use Tools

The LLM autonomously decides whether and when to invoke a tool based on:

1. The user's prompt.
2. The agent's `instructions` — mentioning the tool by name or describing its capabilities helps the LLM understand when to reach for it.
3. The tool's schema (name, description, parameters).

If the agent never uses a tool you expect it to use, improve the `instructions` to explicitly mention it. For example, in `src/demo3_hosted_mcp.py`:

```python
instructions=(
    "You are the Event Coordinator Specialist ... "
    "Use the sequential-thinking tool to break down the planning into clear steps before answering."
)
```

The explicit mention of "sequential-thinking tool" guides the LLM to invoke it.

---

## 5. Core Concepts: Structured Output

### Why Structured Output?

Free-form text is fine for chat, but automation requires machine-readable data. Structured output constrains the LLM to produce valid JSON conforming to a schema you define.

### How It Works

1. Define a Pydantic `BaseModel`:

```python
from pydantic import BaseModel

class VenueInfoModel(BaseModel):
    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0

class VenueOptionsModel(BaseModel):
    options: list[VenueInfoModel]
```

2. Pass the model class as `response_format` when calling `run()`:

```python
response = await agent.run(
    "Find venue options for a corporate holiday party ...",
    response_format=VenueOptionsModel,
)
```

3. The SDK generates a JSON Schema from the Pydantic model and sends it to Foundry. The LLM constrains its output to match that schema.

### Accessing the Result

- **`response.value`** — a typed Pydantic instance (e.g., `VenueOptionsModel`) when the backend successfully parsed the response. This is the preferred path.
- **`response.text`** — the raw text string. Used as a fallback.

### The Fallback Pattern

In some environments or SDK versions, `response.value` may be `None` even though the LLM returned valid JSON in `response.text`. The demo (`src/demo4_structured_output.py`) handles this:

```python
venue_options = getattr(response, "value", None)
if venue_options:
    # Use the typed object directly
    ...
    return

# Fallback: parse from .text
text = (getattr(response, "text", "") or "").strip()
if text.startswith("{") and text.endswith("}"):
    try:
        venue_options = VenueOptionsModel.model_validate_json(text)
    except Exception:
        venue_options = None
```

### Best Practices

- Use `Optional` fields (or `| None`) with sensible defaults so the model can omit unknown values.
- Provide `float` defaults (e.g., `0.0`) rather than leaving fields required when the LLM may not have the data.
- Always implement the fallback path — it costs very little and prevents silent failures.

---

## 6. Core Concepts: Workflows

### Why Workflows?

A single agent is powerful, but real business processes require **controlled sequencing**: research first, then plan, then budget, then finalize. Workflows give you that control while keeping each agent focused on its specialty.

### WorkflowBuilder API

The framework offers two patterns for building workflows. Both produce the same runtime graph.

#### Direct Pattern (used in `src/demo5_workflow_edges.py`)

You create agent instances first, then wire them together:

```python
builder = WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
workflow = (
    builder.set_start_executor(coordinator)
    .add_edge(coordinator, venue)
    .add_edge(venue, catering)
    .add_edge(catering, budget_analyst)
    .add_edge(budget_analyst, booking)
    .build()
)
```

#### Factory Pattern (used in `entities/event_planning_workflow/workflow.py`)

You register callable factories that return agents. The runtime calls them when needed. This pattern supports deferred validation — the factory only runs when the workflow actually executes, not at import time:

```python
workflow = (
    WorkflowBuilder(name="Event Planning Workflow", max_iterations=30)
    .register_agent(create_coordinator_agent, "coordinator")
    .register_agent(create_venue_agent, "venue")
    .register_agent(create_catering_agent, "catering")
    .register_agent(create_budget_analyst_agent, "budget_analyst")
    .register_agent(create_booking_agent, "booking", output_response=True)
    .set_start_executor("coordinator")
    .add_edge("coordinator", "venue")
    .add_edge("venue", "catering")
    .add_edge("catering", "budget_analyst")
    .add_edge("budget_analyst", "booking")
    .build()
)
```

With `register_agent()`, edges are defined using **string names** rather than agent instances. The `output_response=True` flag on the final agent tells the workflow that this agent's output is the workflow's overall output.

### Edge Semantics

Each edge means: "when agent A completes, pass its output as context to agent B." The downstream agent sees the upstream output as part of its input conversation.

### Streaming Events

When you call `workflow.run_stream(prompt)`, you receive an async iterator of typed events:

| Event Type | When It Fires | Key Attributes |
|---|---|---|
| `AgentRunUpdateEvent` | An agent is producing incremental output | `executor_id` |
| `ExecutorCompletedEvent` | An agent has finished its run | `executor_id`, `data` |
| `WorkflowOutputEvent` | The entire workflow has completed | `data` |

The demo (`src/demo5_workflow_edges.py`) uses these events for real-time progress display:

```python
async for event in workflow.run_stream(prompt):
    if isinstance(event, AgentRunUpdateEvent):
        if event.executor_id != last_executor_id:
            print(f"-> {event.executor_id}")
            last_executor_id = event.executor_id
    elif isinstance(event, ExecutorCompletedEvent):
        if event.data is not None:
            completed[event.executor_id] = event.data
    elif isinstance(event, WorkflowOutputEvent):
        final_output = event.data
```

### Resource Management with AsyncExitStack

When a workflow requires multiple agents, you need a reliable way to clean up all of them. `src/demo5_workflow_edges.py` demonstrates this with an `AsyncExitStack`:

```python
from contextlib import AsyncExitStack

stack = AsyncExitStack()
cred = await stack.enter_async_context(AzureCliCredential())
client = await stack.enter_async_context(AzureAIAgentClient(credential=cred))

async def agent_factory(**kwargs):
    return await stack.enter_async_context(client.as_agent(**kwargs))
```

Calling `await stack.aclose()` in a `finally` block closes every agent, the client, and the credential in reverse order.

---

## 7. DevUI

DevUI is a **development-only** sample application shipped in the `agent-framework-devui` package. It is **not intended for production**.

### Entity Discovery

DevUI discovers agents and workflows by scanning an `entities/` directory. Each sub-directory is a Python package that must export either `agent` or `workflow` from its `__init__.py`:

```
entities/
  event_planning_workflow/
    __init__.py          # exports `workflow`
    workflow.py          # defines `workflow = WorkflowBuilder(...).build()`
```

The `__init__.py` in this workshop:

```python
"""DevUI entity export."""
from .workflow import workflow
```

### The `serve()` Function

`src/demo6_devui.py` launches DevUI:

```python
from agent_framework.devui import serve

serve(
    entities=[workflow],
    host="0.0.0.0",
    port=8080,
    auto_open=True,
)
```

| Parameter | Default | Purpose |
|---|---|---|
| `entities` | *(required)* | List of agent or workflow objects to serve |
| `host` | `"0.0.0.0"` | Bind address |
| `port` | `8080` | Listening port |
| `auto_open` | `True` | Open a browser tab automatically |

### What DevUI Provides

- **Web UI** at `http://localhost:8080` — a chat interface for interacting with your agents/workflows.
- **OpenAI-compatible API** at `/v1` — you can point any OpenAI-compatible client at it.
- **OTel tracing display** — if OpenTelemetry is configured, DevUI shows spans inline.

### Import-Time vs. Runtime Validation

The factory pattern (`register_agent()`) is preferred for DevUI because it **defers validation**. Environment variables, DNS checks, and tool requirements are only validated when the workflow actually runs — not when DevUI imports the entity. This allows DevUI to start, list entities, and show its UI even before the user has configured all required environment variables.

---

## 8. Observability with OpenTelemetry

The framework integrates with OpenTelemetry (OTel) for tracing agent runs and tool invocations. All demos in this workshop include an optional OTel setup:

```python
from agent_framework.observability import configure_otel_providers
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

class _DemoSpanExporter(SpanExporter):
    def export(self, spans):
        for s in spans:
            attrs = dict(getattr(s, "attributes", None) or {})
            agent = attrs.get("gen_ai.agent.name", "-")
            tool = attrs.get("gen_ai.tool.name", "-")
            op = attrs.get("gen_ai.operation.name", "-")
            kind = "TOOL" if "gen_ai.tool.name" in attrs else "AGENT"
            print(f"[{kind}] name={s.name} op={op} agent={agent} tool={tool}")
        return SpanExportResult.SUCCESS

configure_otel_providers(exporters=[_DemoSpanExporter()])
```

### Key Span Attributes

| Attribute | Meaning |
|---|---|
| `gen_ai.agent.name` | Name of the agent that produced the span |
| `gen_ai.tool.name` | Name of the tool that was invoked |
| `gen_ai.operation.name` | The operation (e.g., `invoke_agent`, `run_tool`) |
| `gen_ai.tool.call.id` | Unique ID of a specific tool call |

### Production Usage

In production, replace the demo exporter with a real backend (Azure Monitor, Jaeger, Zipkin). The `configure_otel_providers()` call accepts standard OTel exporters.

> **Note:** OpenTelemetry is optional in this workshop. The demos gracefully skip OTel setup if the packages are not installed.

---

## 9. MCP (Model Context Protocol) — Deep Dive

### What Is MCP?

MCP is a **JSON-RPC 2.0** protocol that standardizes how an LLM-based application communicates with external tools. Think of it as "USB-C for AI tools" — any MCP client can talk to any MCP server, regardless of which LLM or framework is behind them.

### Architecture

MCP defines three roles:

| Role | Responsibility |
|---|---|
| **Host** | The application that the user interacts with (e.g., your Python script, an IDE) |
| **Client** | The component inside the host that maintains a 1:1 session with an MCP server |
| **Server** | A lightweight program that exposes tools, resources, or prompts |

In this workshop, the Agent Framework SDK acts as both Host and Client. The MCP server is `@modelcontextprotocol/server-sequential-thinking`, launched via `npx`.

### Transport

| Transport | Mechanism | Use Case |
|---|---|---|
| **stdio** | stdin/stdout of a child process | Local tools (this workshop) |
| **SSE** | HTTP Server-Sent Events | Remote / shared tools |

`MCPStdioTool` uses stdio transport. The SDK spawns the MCP server process, sends JSON-RPC messages to its stdin, and reads responses from its stdout.

### Why MCP Matters for Enterprise

1. **Standardized responsibility boundaries** — the tool's behavior is defined by the MCP server, not the LLM framework. Teams can own their tools independently.
2. **Consent and data privacy** — the protocol encodes what data the server needs and what it returns. This makes policy enforcement tractable.
3. **Ecosystem reuse** — an MCP server built for Claude Desktop works identically with Agent Framework, VS Code Copilot, or any other MCP client.

> **Specification:** [MCP Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)

---

## 10. A2A (Agent-to-Agent Protocol) — Overview

### What Is A2A?

Where MCP connects agents to **tools**, A2A connects agents to **other agents** — potentially across organizations. It standardizes how one agent can discover, communicate with, and delegate tasks to another.

### Key Concepts

| Concept | Purpose |
|---|---|
| **Agent Card** | A machine-readable description of an agent's capabilities, published at a well-known URL |
| **Task** | The unit of work exchanged between agents; includes lifecycle states (submitted, working, completed, failed) |
| **Identity** | Each agent request carries identity claims so the receiving agent can make authorization decisions |

### Relationship to MCP

MCP and A2A are **complementary**, not competing:

- **MCP** = an agent talks to a **tool** (structured I/O, no autonomy on the tool side).
- **A2A** = an agent talks to another **agent** (both sides have autonomy, identity, and potentially different owners).

### The Identity Challenge

When Agent A delegates to Agent B, a critical question arises: "Under whose authority does Agent B act?" A2A addresses this by propagating identity claims through the protocol, but the governance policies are yours to define.

> **Specification:** [A2A Protocol](https://a2a-protocol.org/latest/)

---

## 11. Production Considerations

### The 4 Axes Framework

When moving from workshop demos to production, consider four axes:

#### 1. Boundary

Protocols like MCP and A2A establish **where one component's responsibility ends and another's begins**. Without clear boundaries, every change to a tool or downstream agent risks breaking the entire system.

#### 2. Contract

Structured output (§5) transforms the LLM from a free-text generator into an **automation component** with a defined output schema. Downstream systems can parse, validate, and act on the response without brittle text extraction.

#### 3. Continuation

Long-running workflows may need to **pause and resume** — for human approval, external events, or error recovery. The current SDK supports single-run execution; for production, design checkpointing into your workflow orchestration layer.

#### 4. Observability

OpenTelemetry tracing (§8) provides the audit trail needed for **governance, debugging, and cost attribution**. In production, export spans to Azure Monitor or another APM backend and build dashboards for agent execution patterns.

### Error Handling Patterns

The demos in this workshop demonstrate several error-handling patterns worth adopting:

- **Fail-fast on missing configuration** — `_require_env()` raises a `RuntimeError` with an actionable message before any network call.
- **DNS pre-check** — `_check_project_endpoint_dns()` resolves the Foundry endpoint hostname before calling the API, catching private DNS issues immediately.
- **Command existence check** — `_require_command()` validates that `npx` (or other executables) exist on PATH before spawning MCP servers.
- **ServiceResponseException handling** — the demos catch `ServiceResponseException` and translate common errors (model not found, 403 Forbidden) into messages that tell the user exactly what to check.
- **Preserve exception chains** — `raise ... from ex` keeps the original exception traceable.

### Environment Variable Management

This workshop uses a **fill-only pattern** for `.env` loading:

```python
_dotenv = dotenv_values(_DOTENV_PATH)
for _k, _v in _dotenv.items():
    if _v is None:
        continue
    _existing = os.getenv(_k)
    if _existing is None or not _existing.strip():
        os.environ[_k] = _v
```

This approach:

1. Reads `.env` values via `dotenv_values()` (does **not** modify `os.environ` automatically).
2. Only sets a variable if it is **missing or empty** in the current environment.
3. Preserves explicit overrides (e.g., `VAR=value python script.py`).

This matters in Dev Containers and Codespaces, where `containerEnv` may inject environment variables as **empty strings**, which `python-dotenv`'s default `load_dotenv()` would not overwrite.

### Data Boundary Implications

Hosted tools run on Azure AI Foundry's infrastructure. When you use `HostedWebSearchTool`, the search query and results flow through Microsoft's Bing grounding service. Evaluate your organization's data policies before sending sensitive queries through hosted tools.

### DevUI Is NOT for Production

DevUI (`agent-framework-devui`) is a development convenience. It has no authentication, no rate limiting, and no hardening. For production serving, build your own API layer or use Azure AI Foundry's deployment capabilities.

---

## 12. Version Awareness

### Pinned Pre-Release

This workshop uses three pinned packages (see `requirements.txt`):

```
agent-framework==1.0.0b260123
agent-framework-azure-ai==1.0.0b260123
agent-framework-devui==1.0.0b260123
```

The `b` prefix (e.g., `1.0.0b260123`) indicates a **pre-release** build. The `--pre` flag in `requirements.txt` enables pip to install it.

### Why This Matters

- Microsoft Learn documentation targets the **latest** version. Parameter names, event types, or import paths may change between releases.
- The code in this repository has been tested against the pinned version. If you upgrade, expect potential breaking changes.
- If a demo fails after a pip upgrade, the first thing to check is whether the API surface changed.

### When in Doubt

1. Check `requirements.txt` for the authoritative version.
2. Look at the working demo code in `src/demo*.py` — these are the tested, known-good API calls.
3. Cross-reference with Microsoft Learn, but remember that docs may be ahead of (or behind) the pinned version.
4. The entity code in `entities/` demonstrates the DevUI integration pattern that works with this specific version.

> **Tip:** Pin your dependencies in any project that uses pre-release SDKs. A `pip install --upgrade` at the wrong time can silently break your entire agent pipeline.

---

*This document was written as a supplementary reference for the hands-on workshop. For the latest official documentation, see [Microsoft Agent Framework on Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview/). Always verify against the pinned version in this repository.*
