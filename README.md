# Getting Started with Microsoft Agent Framework (Python)

Hands-on demos for building AI agents and multi-agent workflows with **Microsoft Agent Framework** in Python, using **Azure AI Foundry Agents** as the primary backend.

This repository is optimized for **VS Code Dev Containers / GitHub Codespaces** and pins pre-release Agent Framework packages for reproducibility.

## What’s inside

### Demos (run from `src/`)

| Demo | File | What it demonstrates |
|---:|---|---|
| 1 | `src/demo1_run_agent.py` | Create and run a Foundry-backed agent (`AzureAIAgentClient(...).as_agent(...)` + `run()`) |
| 2 | `src/demo2_web_search.py` | Add **Hosted Web Search** tool (Bing grounding connection required) |
| 3 | `src/demo3_hosted_mcp.py` | Add a local **MCP stdio tool** via `npx` (sequential-thinking) |
| 4 | `src/demo4_structured_output.py` | **Structured output** with `response_format` + Pydantic + fallbacks |
| 5 | `src/demo5_workflow_edges.py` | **Multi-agent workflow** connected by edges + streaming events |
| 6 | `src/demo6_devui.py` | **DevUI** to visually run/debug a workflow (+ OpenAI-compatible API) |

### Workflow entities (used by DevUI)

- `entities/event_planning_workflow/` (used by Demo 6)
- `entities/ai_genius_workflow/` (extra entity; requires Azure OpenAI config)

## Prerequisites

- Python **3.10+** (Dev Container uses Python **3.11**)
- Azure CLI (Dev Container installs it)
- Access to an **Azure AI Foundry Project** with:
	- a model deployment in **Models + endpoints**
	- appropriate RBAC to run agents

## Quick start (recommended: Dev Container / Codespaces)

1) Open this repo in a Dev Container / Codespaces

2) Create `.env`

If you have `.env.example`, the Dev Container post-create script will copy it to `.env` automatically.
Otherwise, copy it manually and fill values (never commit `.env`).

3) Login to Azure (inside the container)

Use device code login if your environment can’t open a browser:

- `az login --use-device-code`

4) Run a demo

- `python3 -u src/demo1_run_agent.py`

## Environment variables

This repo intentionally uses a **fill-only** `.env` strategy in scripts and entities:
Dev Containers / Codespaces sometimes inject environment variables as **empty strings**, and typical dotenv behavior won’t override them.
These demos load the repo-root `.env` and only fill variables that are unset or empty.

### Required for Azure AI Foundry Agents (Demos 1–6)

| Variable | Required | Notes |
|---|:---:|---|
| `AZURE_AI_PROJECT_ENDPOINT` | ✅ | Must be a Foundry Project endpoint like `https://<account>.services.ai.azure.com/api/projects/<project-id>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | ✅ | The **deployment name** shown in Foundry Project → **Models + endpoints** |

### Required for Hosted Web Search (Demos 2, 4, 5, 6)

| Variable | Required | Notes |
|---|:---:|---|
| `BING_CONNECTION_ID` | ✅ | Foundry project connection ID for “Grounding with Bing Search” (recommended) |

### Required only for Azure OpenAI-based entities (not needed for Demos 1–6)

`entities/ai_genius_workflow/` uses Azure OpenAI. If you want to run it, set:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_KEY` (if using API key auth)

## Run the demos

All commands are executed from the repository root.

### Demo 1 — Run a Foundry-backed agent

- `python3 -u src/demo1_run_agent.py`

### Demo 2 — Hosted Web Search

- `python3 src/demo2_web_search.py`

Requires `BING_CONNECTION_ID` in addition to Foundry variables.

### Demo 3 — MCP stdio tool via `npx`

- `python3 src/demo3_hosted_mcp.py`

Requires Node.js / `npx` (available in the Dev Container).

### Demo 4 — Structured output (`response_format`)

- `python3 -u src/demo4_structured_output.py`

### Demo 5 — Multi-agent workflow (edges + streaming)

- `python3 -u src/demo5_workflow_edges.py`

Optional: pause before exiting:

- `DEMO_PAUSE=1 python3 -u src/demo5_workflow_edges.py`

### Demo 6 — DevUI (port 8080)

- `python3 -u src/demo6_devui.py`

DevUI will listen on:

- UI: `http://localhost:8080`
- API (OpenAI-compatible): `http://localhost:8080/v1`

Disable browser auto-open (headless environments):

- `DEMO_NO_OPEN=1 python3 -u src/demo6_devui.py`

Change bind host/port:

- `DEVUI_HOST=0.0.0.0 DEVUI_PORT=8082 python3 -u src/demo6_devui.py`

Health check (inside the container):

- `curl -fsS http://localhost:8080/health`

## Dev Container notes

This repo includes a Dev Container configuration under `.devcontainer/`.

- `.devcontainer/Dockerfile` builds a Python 3.11 (Debian bookworm) environment and installs Azure CLI
- `requirements.txt` pins Agent Framework packages (pre-release)
- `.devcontainer/devcontainer.json` forwards **port 8080** for DevUI

Note: `.devcontainer/compose.yaml` does not publish ports at Docker level; port access is typically via **VS Code port forwarding**.

## Troubleshooting

### `Cannot resolve ... via DNS` / `Temporary failure in name resolution`

Many scripts preflight DNS resolution for the Foundry project endpoint.
If your Foundry project is behind private networking / private DNS, a container or Codespaces may not be able to resolve it.

### `Failed to resolve model info for: ...`

`AZURE_AI_MODEL_DEPLOYMENT_NAME` must match a deployment name in Foundry Project → **Models + endpoints**.

### `Hosted web search requires a Bing connection`

Set `BING_CONNECTION_ID` to the Foundry project connection ID.

### 401 / 403 authentication and RBAC

- Ensure you ran `az login` inside the container
- Verify your account has permissions on the Foundry project (and any required connections)

### `npx` not found / MCP server fails

Demo 3/5 rely on starting an MCP stdio server using `npx`.
If you run outside the Dev Container, install Node.js and ensure `npx` is on PATH.

## References (official docs)

Docs often track the **latest** SDK; this repo pins specific pre-release versions. If something differs, prefer the code in this repository.

- Agent Framework overview: https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview/
- Azure AI Foundry Agents (Python): https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
- Run agent tutorial: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- Agent tools (hosted tools, MCP tools): https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python
- HostedWebSearchTool API: https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.hostedwebsearchtool?view=agent-framework-python-latest
- Structured output: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
- Agents in workflows: https://learn.microsoft.com/en-us/agent-framework/tutorials/workflows/agents-in-workflows?pivots=programming-language-python
- DevUI overview: https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
- DevUI directory discovery: https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
- DevUI API reference: https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference

## License

Released under the MIT license.

## Author

- GitHub: https://github.com/shinyay
- X (Twitter): https://x.com/yanashin18618
- Mastodon: https://mastodon.social/@yanashin
