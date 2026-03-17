---
layout: cheatsheet
title: "Exercise 5 — Walkthrough"
parent_step: 5
permalink: /cheatsheet/5/
---

# Demo 5 — Multi-agent Workflow (Event Planning Workflow)

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/agents-in-workflows?pivots=programming-language-python
```

This demo **chains multiple specialized agents sequentially using a workflow (edge)**
to divide and integrate event planning tasks.

## Objectives
- Split agents by role (specialization) and **fix the order with Edges** to build a stable pipeline
- Use Hosted tools (Web Search / Code Interpreter) and MCP tool (sequential-thinking) within the workflow
- (Optional) Output OTel spans in a single line to observe "which agent/tool was called"

The workflow in this demo follows this order:

1. `coordinator` (overall planning + sequential-thinking)
2. `venue` (venue research: Hosted Web Search)
3. `catering` (catering research: Hosted Web Search)
4. `budget_analyst` (cost estimation and allocation: Hosted Code Interpreter)
5. `booking` (final integration: outputs plan in markdown)

---

## Prerequisites

### Common (Foundry Agents)
- Demo 2 is complete (Foundry env vars are configured)
- `agent-framework-azure-ai` is installed
- `az login` completed (this demo uses AzureCliCredential by default)

Required env vars:

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"
```

### Additional (specific to this demo)

#### 1) sequential-thinking (MCP stdio)
- `node` / `npx` must be available (`MCPStdioTool` launches `npx ...` locally)

#### 2) Hosted Web Search (Bing connection)
This demo performs web searches for venues/catering, so a Bing grounding connection ID is required.

Set one of the following:

- `BING_CONNECTION_ID` (or `BING_PROJECT_CONNECTION_ID`)
- Or for Custom Search:
  - `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`
  - (or `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID` + `BING_CUSTOM_SEARCH_INSTANCE_NAME`)

> `src/demo5_workflow_edges.py` explicitly loads the repository root `.env` and only fills in unset/empty env vars (mitigating the empty-string injection issue in Dev Container / Codespaces).

---

## Steps

### Step 1. Verify `.env` (recommended)
At minimum, the following are required:

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `BING_CONNECTION_ID` (or an equivalent Bing connection setting)

### Step 2. Log in (Entra ID)

```bash
az login --use-device-code
```

### Step 3. Run

```bash
python3 -u src/demo5_workflow_edges.py
```

(Optional) To pause after execution:

```bash
DEMO_PAUSE=1 python3 -u src/demo5_workflow_edges.py
```

Expected behavior:

- `Workflow Result:` is displayed after `Running workflow...`
- The output appears as multiple steps (results from each specialist)
- (In environments with OTel enabled) Logs like `[TOOL] ... tool=...` / `[AGENT] ...` will be interspersed

---

## Technical Notes (Design decisions)

- The workflow follows the pattern of "dividing event planning among *multiple specialists*, with booking integrating at the end"
- The pinned SDK in this repository uses `AzureAIAgentClient(...).as_agent(...)` instead of `create_agent(...)` for safety, so the implementation is based on `as_agent`

---

## Troubleshooting

### `npx` not found
- Install Node.js (usually not needed in the dev container)

### No Bing connection
- Set `BING_CONNECTION_ID` (or `BING_PROJECT_CONNECTION_ID`)

### 403 / Forbidden
- Have you completed `az login`?
- Does the executing user have RBAC assigned on the Foundry Project / Hub?

### Failed to resolve model info
- Is `AZURE_AI_MODEL_DEPLOYMENT_NAME` set to the **deployment name from Models + endpoints** in Foundry?

### DNS resolution fails before starting
- Check your Private networking / private DNS configuration
  - The included script performs a DNS pre-check and provides a clear error message

---

## Next Demo (DevUI)
In Demo 6, we **visualize this "Event Planning Workflow" with DevUI**.
→ Open `demo6.md` to continue.
