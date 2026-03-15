# Exercise 5 — Build a Multi-Agent Workflow

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 3 — Orchestration | ⭐⭐⭐ Advanced | 30–40 min |

## Learning Objectives

By the end of this exercise you will be able to:

1. Create multiple specialist agents, each with different tools
2. Connect agents into a pipeline using `WorkflowBuilder` edges
3. Consume streaming events (`AgentRunUpdateEvent`, `ExecutorCompletedEvent`, `WorkflowOutputEvent`) to monitor workflow progress
4. Understand event-driven orchestration — why ordering, state, and business-process control matter

---

## Prerequisites

| Requirement | How to verify |
|-------------|--------------|
| Exercises 1–4 completed | You are comfortable creating agents with tools and structured output |
| Azure CLI logged in | `az account show` (should return your subscription) |
| `.env` configured | `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and Bing connection vars set |
| `npx` available | `npx --version` (required for the MCP sequential-thinking tool) |
| Bing connection configured | `BING_CONNECTION_ID` (or custom Bing vars) set in `.env` |

---

## Background

### Why Workflows?

In Exercises 1–4 you ran a single agent at a time. Real-world scenarios often require **multiple specialists** that hand off work in a defined order — this is a **workflow**.

Workflows give you:

- **Business-process control** — enforce the order in which agents run
- **State passing** — each agent receives the output of the previous one
- **Observability** — streaming events let you track progress in real time
- **Reliability** — the framework manages agent lifecycle and error propagation

### The WorkflowBuilder API

The framework provides `WorkflowBuilder` to assemble a directed graph of agents:

```
WorkflowBuilder()           # create a builder
  .set_start_executor(a)    # mark agent 'a' as the entry point
  .add_edge(a, b)           # a → b (b runs after a completes)
  .add_edge(b, c)           # b → c
  .build()                  # returns a runnable Workflow
```

Call `workflow.run_stream(prompt)` to execute. It yields events as each agent progresses:

| Event Type | Purpose |
|-----------|---------|
| `AgentRunUpdateEvent` | An agent is actively producing output — use `event.executor_id` to identify which one |
| `ExecutorCompletedEvent` | An agent finished — `event.executor_id` + `event.data` contain its result |
| `WorkflowOutputEvent` | The entire workflow completed — `event.data` is the final output |

### The Event Planning Scenario

In this exercise you will build a 5-agent pipeline that plans a corporate event:

```
Coordinator → Venue → Catering → Budget Analyst → Booking
```

Each agent specialises in one aspect and passes its work to the next:

| Agent | Role | Tool |
|-------|------|------|
| **coordinator** | Creates a step-by-step plan for the team | `MCPStdioTool` (sequential-thinking) |
| **venue** | Recommends venues based on requirements | `HostedWebSearchTool` (Bing) |
| **catering** | Proposes food & beverage options | `HostedWebSearchTool` (Bing) |
| **budget_analyst** | Estimates costs and allocates budget | `HostedCodeInterpreterTool` |
| **booking** | Synthesises all outputs into a final event plan | _(no tools — text synthesis only)_ |

---

## Your Task

Open `starter.py` in this directory. You will see **8 TODO markers** inside `async def main()`. The infrastructure code (imports, env loading, agent factory, helpers) is provided — your job is to wire up the agents, build the workflow, and handle the streaming events.

### Step 1 — Create the Coordinator Agent (TODO 1)

Create an agent named `"coordinator"` with `MCPStdioTool` for sequential thinking:

- **name**: `"coordinator"`
- **instructions**: Describe the agent as an event coordinator who creates step-by-step plans
- **tools**: `MCPStdioTool(name="sequential-thinking", command="npx", load_prompts=False, args=["-y", "@modelcontextprotocol/server-sequential-thinking"])`

### Step 2 — Create the Venue Agent (TODO 2)

Create an agent named `"venue"` with `HostedWebSearchTool`:

- **name**: `"venue"`
- **instructions**: Describe the agent as a venue specialist
- **tools**: `HostedWebSearchTool(description="Search the web for current information using Bing", tool_properties=bing_props)`

### Step 3 — Create the Catering Agent (TODO 3)

Create an agent named `"catering"` with `HostedWebSearchTool`:

- **name**: `"catering"`
- **instructions**: Describe the agent as a catering coordinator
- **tools**: Same as venue (Bing search with `bing_props`)

### Step 4 — Create the Budget Analyst Agent (TODO 4)

Create an agent named `"budget_analyst"` with `HostedCodeInterpreterTool`:

- **name**: `"budget_analyst"`
- **instructions**: Describe the agent as a budget analyst who uses code for calculations
- **tools**: `HostedCodeInterpreterTool(description="Execute Python code for calculations: budget breakdowns, totals, per-person estimates, and simple what-if analysis.")`

### Step 5 — Create the Booking Agent (TODO 5)

Create an agent named `"booking"` with **no tools** — it synthesises all prior outputs:

- **name**: `"booking"`
- **instructions**: Describe the agent as an event booking specialist who creates a cohesive final plan

### Step 6 — Build the Workflow (TODO 6)

Use `WorkflowBuilder` to chain the five agents:

```
coordinator → venue → catering → budget_analyst → booking
```

Call `.set_start_executor()`, then `.add_edge()` for each connection, then `.build()`.

### Step 7 — Run and Handle Streaming Events (TODO 7)

Call `workflow.run_stream(prompt)` and iterate over events with `async for`:

- **`AgentRunUpdateEvent`**: Print which executor is active (avoid spamming — only print when `executor_id` changes)
- **`ExecutorCompletedEvent`**: Save `event.data` into the `completed` dict keyed by `event.executor_id`
- **`WorkflowOutputEvent`**: Save `event.data` as the `final_output`

### Step 8 — Print Results (TODO 8)

Iterate over the `chain` list and print each completed executor's result using `_print_result_item()`. Fall back to `final_output` if no per-executor completions were captured.

---

## Hints

Work through the hints progressively — try on your own first!

<details>
<summary>💡 Hint 1 — Creating agents</summary>

Each agent is created with `await agent(name=..., instructions=..., tools=[...])`. The `agent` factory was returned by `_create_agent_factory()`. Agents without tools simply omit the `tools` parameter:

```python
coordinator = await agent(
    name="coordinator",
    instructions="You are the Event Coordinator. ...",
    tools=[MCPStdioTool(...)],
)
```

</details>

<details>
<summary>💡 Hint 2 — Building the workflow</summary>

Chain edges to form a linear pipeline. The builder supports fluent chaining:

```python
workflow = (
    WorkflowBuilder()
    .set_start_executor(coordinator)
    .add_edge(coordinator, venue)
    .add_edge(venue, catering)
    .add_edge(catering, budget_analyst)
    .add_edge(budget_analyst, booking)
    .build()
)
```

</details>

<details>
<summary>💡 Hint 3 — Handling streaming events</summary>

Use `isinstance()` to check event types. Track the last executor ID to avoid printing duplicates:

```python
events = workflow.run_stream(prompt)
last_executor_id = None
async for event in events:
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

</details>

<details>
<summary>💡 Hint 4 — Printing results</summary>

Iterate over the expected chain order and print each completed executor's result:

```python
printed_any = False
for executor_id in chain:
    if executor_id not in completed:
        continue
    printed_any = True
    print(f"### {executor_id}")
    _print_result_item(completed[executor_id])
    print()

if not printed_any and final_output is not None:
    _print_result_item(final_output)
```

</details>

---

## Validate Your Work

### 1. Run the check script (offline — no Azure needed)

```bash
bash workshop/exercises/ex5_workflow/check.sh
```

This verifies syntax, required code patterns (WorkflowBuilder, edges, event handling), and that all TODOs are resolved.

### 2. Run against Azure

```bash
python3 -u workshop/exercises/ex5_workflow/starter.py
```

**Expected behaviour:**

- The script connects to your Foundry project and creates 5 agents.
- You see executor progress lines like `-> coordinator`, `-> venue`, etc.
- Each agent runs in sequence — the full workflow takes **2–5 minutes** depending on model speed.
- After completion, you see per-executor results (venue recommendations, catering plans, budget breakdown, final event plan).
- If OpenTelemetry is available, `[AGENT]` and `[TOOL]` span lines appear.

> **Note:** This exercise takes significantly longer than previous ones because 5 agents run sequentially. Be patient — the streaming events let you see progress in real time.

---

## Bonus Challenges

1. **Add a 6th agent** — e.g., a "transportation" specialist that plans logistics between the venue and attendee locations. Insert it between `venue` and `catering` in the edge chain.
2. **Change the edge order** — What happens if you swap `venue` and `catering`? Does the output quality change?
3. **Add error handling per executor** — Wrap the event loop in more granular error handling. What if one agent fails — can you still show partial results?
4. **Experiment with `max_iterations`** — Pass `max_iterations=10` to `WorkflowBuilder()` and observe how it affects workflow behaviour.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Workflow takes > 5 minutes | Normal for 5 sequential agents with tools | Be patient — streaming events show progress. Consider reducing agent instructions if testing |
| `npx` not found | Node.js not installed | Install Node.js or run in the dev container where it is preinstalled |
| Bing connection error | `BING_CONNECTION_ID` not set or invalid | Create a "Grounding with Bing Search" connection in the Foundry portal and set the ID in `.env` |
| `403 Forbidden` | RBAC permissions missing | Ensure your Entra ID has the appropriate role for the Foundry project. Run `az login` to refresh |
| `Failed to resolve model info` | Wrong model deployment name | Check `AZURE_AI_MODEL_DEPLOYMENT_NAME` matches a deployment in your Foundry project's "Models + endpoints" |
| No events from `run_stream` | Possible SDK/endpoint mismatch | Verify `agent-framework` version matches `requirements.txt`. Check that the project endpoint is reachable |
| `RuntimeError: Required command ...` | `npx` not on PATH | Install Node.js or ensure the dev container has it |

---

## Solution Reference

See the complete working solution at: **`src/demo5_workflow_edges.py`**
