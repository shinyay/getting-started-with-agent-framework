# Exercise 6 — Launch DevUI for Your Workflow

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 3 — Orchestration | ⭐⭐⭐ Intermediate | 25–35 min |

## Learning Objectives

By the end of this exercise you will be able to:

1. Create a **DevUI entity** — the directory structure and `__init__.py` that DevUI discovers
2. Understand **entity discovery** — how DevUI finds workflows in entity packages
3. Use **`serve()`** to launch the DevUI development server
4. Access the **web UI** and the **OpenAI-compatible API** (`/v1`) that DevUI provides

---

## Prerequisites

| Requirement | How to verify |
|-------------|--------------|
| Exercise 5 completed | You have a working multi-agent workflow |
| Azure CLI logged in | `az account show` (should return your subscription) |
| `.env` configured | `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and Bing connection vars are set |
| Dependencies installed | `python3 -c "from agent_framework.devui import serve"` succeeds |

---

## Background

### What Is DevUI?

**DevUI** is a development-only sample application bundled with the Agent Framework. It provides a web interface for visually running and debugging workflows — think of it as a local playground for your agents.

> ⚠️ **DevUI is NOT for production.** It is a development/debugging aid only.

### How Entity Discovery Works

DevUI discovers entities from **directories**. Each entity is a Python package (a directory with `__init__.py`) that exports either:

- `agent` — a single agent
- `workflow` — a multi-agent workflow

When you pass `entities=[workflow]` to `serve()`, DevUI registers them and makes them available in the web UI.

### What DevUI Gives You

| Feature | Description |
|---------|-------------|
| **Web UI** | Visual interface at `http://localhost:8080` to run and debug workflows |
| **OpenAI-compatible API** | REST endpoint at `/v1` — compatible with OpenAI client libraries |
| **Entity listing** | Auto-discovers and lists all registered entities |

### The `serve()` Function

`serve()` starts a Uvicorn web server with the DevUI application:

```python
from agent_framework.devui import serve

serve(
    entities=[workflow],   # list of workflow/agent entities
    host="0.0.0.0",        # listen address
    port=8080,             # listen port
    auto_open=True,        # open browser automatically
)
```

---

## Your Task

This exercise has **two parts**: creating the entity package (Part A) and the server launcher (Part B).

### Part A — Entity: Create a Workflow Entity (`starter_entity/`)

Open `starter_entity/workflow.py`. You will find **6 TODO markers**. The helper functions (`.env` loading, DNS check, environment validation, client caching) are provided.

You will build a simplified **3-agent workflow** (coordinator → venue → booking):

#### Step 1 — Create Coordinator Factory (TODO 1)

Create a `create_coordinator_agent()` function that:
- Calls `_validate_environment()` to check all required config
- Gets the cached client via `_get_client()`
- Returns `client.as_agent(name="coordinator", instructions=...)`

#### Step 2 — Create Venue Factory (TODO 2)

Create a `create_venue_agent()` function that:
- Validates environment and gets the client
- Returns an agent with `HostedWebSearchTool` using `_get_bing_tool_properties()`

#### Step 3 — Create Booking Factory (TODO 3)

Create a `create_booking_agent()` function that:
- Validates environment and gets the client
- Returns an agent that synthesizes all prior outputs (no tools needed)

#### Step 4–6 — Build the Workflow (TODO 4–6)

Use `WorkflowBuilder` to wire the agents together:
- Register each agent factory with `.register_agent(factory_fn, "name")`
- Set the start executor to `"coordinator"`
- Add edges: coordinator → venue → booking
- Call `.build()`

### Part B — Server: Create the DevUI Launcher (`starter.py`)

Open `starter.py`. You will find **4 TODO markers**. The port-preflight logic is provided.

#### Step 1 — Import `serve` (TODO 1)

```python
from agent_framework.devui import serve
```

#### Step 2 — Import Your Workflow (TODO 2)

Import the `workflow` object from your `starter_entity` package.

#### Step 3 — Configure Host and Port (TODO 3)

Read `DEVUI_HOST` and `DEVUI_PORT` from environment variables with sensible defaults (`0.0.0.0` and `8080`).

#### Step 4 — Call `serve()` (TODO 4)

Call `serve()` with `entities=[workflow]`, host, port, and `auto_open`.

---

## Hints

Work through the hints progressively — try on your own first!

<details>
<summary>💡 Hint 1 — Entity __init__.py</summary>

The `starter_entity/__init__.py` is already provided. It exports `workflow` from `.workflow`. This is the minimum DevUI needs to discover the entity.

</details>

<details>
<summary>💡 Hint 2 — Agent factory pattern</summary>

Each factory function follows the same pattern — DevUI calls these lazily when a workflow run starts:

```python
def create_some_agent():
    _validate_environment()
    client = _get_client()
    return client.as_agent(
        name="agent_name",
        instructions="...",
        tools=[...],  # optional
    )
```

</details>

<details>
<summary>💡 Hint 3 — WorkflowBuilder pattern</summary>

```python
workflow = (
    WorkflowBuilder(name="...", max_iterations=30)
    .register_agent(create_coordinator_agent, "coordinator")
    .register_agent(create_venue_agent, "venue")
    .register_agent(create_booking_agent, "booking", output_response=True)
    .set_start_executor("coordinator")
    .add_edge("coordinator", "venue")
    .add_edge("venue", "booking")
    .build()
)
```

The last agent should have `output_response=True` so its response becomes the workflow output.

</details>

<details>
<summary>💡 Hint 4 — serve() call</summary>

```python
serve(
    entities=[workflow],
    host=host,
    port=port,
    auto_open=not no_open,
)
```

</details>

---

## Validate Your Work

### 1. Run the check script (offline — no Azure needed)

```bash
bash workshop/exercises/ex6_devui/check.sh
```

This verifies syntax, entity structure, required code patterns, and that all TODOs are resolved.

### 2. Launch DevUI

```bash
python3 -u workshop/exercises/ex6_devui/starter.py
```

**Expected behaviour:**

- The server starts on `http://localhost:8080` (or your configured port).
- Your browser opens automatically (unless `DEMO_NO_OPEN=1` or headless environment).
- The web UI shows your workflow entity listed and ready to run.
- You can submit a prompt and watch agents execute in sequence.

### 3. Test the health / API endpoint

```bash
curl -s http://localhost:8080/v1/models | python3 -m json.tool
```

This should return a JSON response listing available models/entities.

---

## Bonus Challenges

1. **Add a 4th agent** — Extend the workflow with a `catering` agent between `venue` and `booking`. Update the edges accordingly.
2. **Try the `/v1` API** — Use the OpenAI-compatible endpoint with `curl` or the `openai` Python library to interact with your workflow programmatically:
   ```bash
   curl http://localhost:8080/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "starter_entity", "messages": [{"role": "user", "content": "Plan a team offsite"}]}'
   ```
3. **Custom port** — Set `DEVUI_PORT=9090` and verify everything still works.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: workshop.exercises...` | `sys.path` doesn't include repo root | Ensure the repo-root path insertion in `starter.py` is correct |
| Entity not detected in DevUI | Missing `__init__.py` in entity directory | Verify `starter_entity/__init__.py` exists and exports `workflow` |
| `RuntimeError: DevUI cannot start because 0.0.0.0:8080 is already in use` | Port already occupied | Stop the other process or set `DEVUI_PORT=8081` |
| Browser doesn't open | Headless environment (Codespaces, SSH) | Expected — access via the forwarded port URL in your Codespaces/VS Code |
| `RuntimeError: Required environment variable ...` | Missing or empty env var | Check `.env` at the repo root |
| `Cannot resolve ... host via DNS` | Foundry project uses private networking | Use a public endpoint or run from a network that can resolve the private DNS |
| `ModuleNotFoundError: agent_framework.devui` | `agent-framework-devui` not installed | Run `pip install -r requirements.txt` |

---

## Solution Reference

See the complete working solutions at:

- **Server:** `src/demo6_devui.py`
- **Entity:** `entities/event_planning_workflow/`
