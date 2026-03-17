---
layout: cheatsheet
title: "Exercise 6 — Walkthrough"
parent_step: 6
permalink: /cheatsheet/6/
---

# Demo 6 — DevUI (Visualize and debug workflows)

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference
```

## Objectives
- Launch DevUI and **observe workflow execution in the UI**
- Visually track "which step ran when / what the inputs and outputs were"
- **Register a workflow directly** using `serve()` and display it

> DevUI is a sample app for development purposes and is not intended for production use.

---

## Prerequisites
- Demo 5 is complete (Foundry Agents + Bing + npx are working)
- `agent-framework-devui` is installed

Required env vars (same as Demo 5):

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `BING_CONNECTION_ID` (or `BING_PROJECT_CONNECTION_ID`)

Additional:
- `npx` must be available (coordinator launches sequential-thinking MCP)

Note:
- DevUI is a sample app for local development (not intended for production use)
- Port forwarding is required for Codespaces / Dev Container (see below)

---

## How to proceed (using `serve()`)
Register a workflow and launch DevUI with `serve(entities=[workflow], auto_open=True)`.

---

# A) Launch DevUI with `serve()` (recommended)

This repository provides the following files so you can view the "Event Planning Workflow" in DevUI:

- `src/demo6_devui.py` (DevUI launch script)
- `entities/event_planning_workflow/` (DevUI entity: exports the workflow)

## Step A-1. Run

```bash
python3 -u src/demo6_devui.py
```

If you get `address already in use` (port is in use), you can resolve it with either of the following:

- Stop the already running DevUI (or other process)
- Or launch on a different port (e.g., `DEVUI_PORT=8082`)

Once started, DevUI listens on `http://localhost:8081` (recommended).

For Codespaces / Dev Container:
- Forward port `8081`

Note:
- In environments where automatic browser opening is not needed or fails, you can disable it as follows:

```bash
DEMO_NO_OPEN=1 python3 -u src/demo6_devui.py
```

## Step A-2. Run the workflow in the UI
1. Open DevUI (`http://localhost:8081`)
2. Select "Event Planning Workflow" from the Entities list
3. Paste the following as input and run:
    - `Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle`
4. Observe the execution proceeding in order: coordinator → venue → catering → budget_analyst → booking

---

## Checking DevUI status / Stopping

### Checking status (start here)

#### 1) Check via the Ports panel (recommended for Dev Container / Codespaces)
- Open the **PORTS** tab at the bottom of VS Code
- If there is a row for `8081` and the Running Process shows `python3 -u src/demo6_devui.py`, it is running

#### 2) Check via /health (most reliable)
If the following returns `{"status":"healthy"...}` from inside the container, it is running:

```bash
curl -fsS http://localhost:8081/health
```

#### 3) Check which process is listening (Linux/Dev Container)

```bash
ss -ltnp | grep ':8081'
```

### Stopping

#### 1) Ctrl+C for foreground execution
If you are running `python3 -u src/demo6_devui.py` in a terminal, pressing `Ctrl+C` in that terminal is the safest approach.

#### 2) Stop by specifying the PID
Stop the PID found via `ss -ltnp | grep ':8081'`:

```bash
kill <PID>
```

#### 3) Find and stop all (last resort)
If you want to stop only the DevUI launch processes:

```bash
pkill -f 'src/demo6_devui.py'
```

> Caution: `pkill -f` stops all matching processes. If you are concerned about unintended termination, use a specific PID instead.

# B) Launch via directory discovery (CLI) (optional)

If you want to discover entities using the existing DevUI CLI, you can also launch with:

```bash
devui ./entities --host 0.0.0.0 --port 8081 --no-open
```

In this case, entities under `entities/` (e.g., `event_planning_workflow`) will appear in the list.

---

# C) Call DevUI via the OpenAI-compatible API (optional)

DevUI provides an OpenAI-compatible Responses API with `http://localhost:8081/v1` as the base URL.

Example (Python):
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8081/v1", api_key="not-needed")

resp = client.responses.create(
    metadata={"entity_id": "event_planning_workflow"},
    input="Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
)

print(resp.output[0].content[0].text)
```

Note:
- The DevUI base URL is `http://localhost:8081/v1`
- The `entity_id` in `metadata={"entity_id": "ai_genius_workflow"}` must match the ID visible at `/v1/entities`

---

## Troubleshooting

### Entity is not detected
- Does `entities/<name>/__init__.py` exist?
- Does `__init__.py` export a `workflow` variable?
- Are there any syntax errors?
- Is the directory directly under the path passed to `devui`?

### Environment variables are not loaded
- Is the `.env` file in the correct location (directly under entities or under each entity)?
- You can use `--reload` to reload

Note:
- DevUI can automatically load `.env` files as part of its official specification (from the entities root / under each entity)
- However, this repository also uses an implementation that references the **repository root `.env`** to maintain consistency with the existing demos (Demo 1 onwards)
    - Ideally, you would consolidate to one approach, but hands-on reproducibility is prioritized here

### DNS resolution fails before starting (Azure OpenAI)
If the host in `AZURE_OPENAI_ENDPOINT` cannot be DNS-resolved from inside the Dev Container, it will fail at startup or during execution.

- Error example: `Cannot resolve AZURE_OPENAI_ENDPOINT host via DNS`
- Resolution: Review your Private networking / private DNS configuration, or run from a network where DNS resolution is possible

---

## What to do next (advanced)
- Enable OpenTelemetry tracing with `--tracing` to further trace tool calls and execution flow
- Integrate the tools from Demo 2/3 (Web Search / MCP) into workflow agents to get closer to "real-world use cases"

Reference:
- DevUI collects and displays OpenTelemetry spans emitted by Agent Framework (DevUI itself does not create the spans)
