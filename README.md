# Getting Started with Microsoft Agent Framework (Python)

Hands-on workshop for building AI agents and multi-agent workflows with **Microsoft Agent Framework** in Python, using **Azure AI Foundry Agents** as the primary backend.

This repository is optimized for **VS Code Dev Containers / GitHub Codespaces** and pins pre-release Agent Framework packages for reproducibility. The `workshop/` directory contains progressive exercises; `src/` holds reference solutions.

## What’s inside

### Reference Solutions (in `src/`)

| Exercise | Solution File | What it covers |
|---:|---|---|
| 1 | `src/demo1_run_agent.py` | Create and run a Foundry-backed agent (`AzureAIAgentClient(...).as_agent(...)` + `run()`) |
| 2 | `src/demo2_web_search.py` | Add **Hosted Web Search** tool (Bing grounding connection required) |
| 3 | `src/demo3_hosted_mcp.py` | Add a local **MCP stdio tool** via `npx` (sequential-thinking) |
| 4 | `src/demo4_structured_output.py` | **Structured output** with `response_format` + Pydantic + fallbacks |
| 5 | `src/demo5_workflow_edges.py` | **Multi-agent workflow** connected by edges + streaming events |
| 6 | `src/demo6_devui.py` | **DevUI** to visually run/debug a workflow (+ OpenAI-compatible API) |

### Workflow entities (used by DevUI)

- `entities/event_planning_workflow/` (used by Exercise 6)
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

4) Run an exercise

- `python3 -u src/demo1_run_agent.py`

## Environment variables

This repo intentionally uses a **fill-only** `.env` strategy in scripts and entities:
Dev Containers / Codespaces sometimes inject environment variables as **empty strings**, and typical dotenv behavior won’t override them.
Exercise scripts and solutions load the repo-root `.env` and only fill variables that are unset or empty.

### Required for Azure AI Foundry Agents (Exercises 1–6)

| Variable | Required | Notes |
|---|:---:|---|
| `AZURE_AI_PROJECT_ENDPOINT` | ✅ | Must be a Foundry Project endpoint like `https://<account>.services.ai.azure.com/api/projects/<project-id>` |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | ✅ | The **deployment name** shown in Foundry Project → **Models + endpoints** |

### Required for Hosted Web Search (Exercises 2, 4, 5, 6)

| Variable | Required | Notes |
|---|:---:|---|
| `BING_CONNECTION_ID` | ✅ | Foundry project connection ID for “Grounding with Bing Search” (recommended) |

### Required only for Azure OpenAI-based entities (not needed for Exercises 1–6)

`entities/ai_genius_workflow/` uses Azure OpenAI. If you want to run it, set:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_KEY` (if using API key auth)

## Run the exercises

All commands are executed from the repository root.

### Exercise 1 — Run a Foundry-backed agent

- `python3 -u src/demo1_run_agent.py`

### Exercise 2 — Hosted Web Search

- `python3 src/demo2_web_search.py`

Requires `BING_CONNECTION_ID` in addition to Foundry variables.

### Exercise 3 — MCP stdio tool via `npx`

- `python3 src/demo3_hosted_mcp.py`

Requires Node.js / `npx` (available in the Dev Container).

### Exercise 4 — Structured output (`response_format`)

- `python3 -u src/demo4_structured_output.py`

### Exercise 5 — Multi-agent workflow (edges + streaming)

- `python3 -u src/demo5_workflow_edges.py`

Optional: pause before exiting:

- `DEMO_PAUSE=1 python3 -u src/demo5_workflow_edges.py`

### Exercise 6 — DevUI (port 8080)

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

Exercises 3 and 5 rely on starting an MCP stdio server using `npx`.
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

## Hands-On Workshop

This repository also includes a **hands-on workshop** for instructor-led or self-paced learning:

- **Workshop materials**: `workshop/README.md` — 7 progressive exercises from fill-in-the-blank to build-from-scratch
- **Reference docs**: `workshop/reference/` — Agent Framework deep-dive guide, API cheat sheet, curated links
- **Instructor guide**: `workshop/instructor/facilitator-guide.md`

The workshop preserves all existing demo files (`src/demo*.py`) as reference solutions.

See [`workshop/README.md`](workshop/README.md) for the full agenda and setup instructions.

## License

Released under the MIT license.

## Author

- GitHub: https://github.com/shinyay
- X (Twitter): https://x.com/yanashin18618
- Mastodon: https://mastodon.social/@yanashin

---

## Workshop Pages Theme (GitHub Pages)

This repository uses `shinyay/workshop-pages-theme` as a Jekyll remote theme for GitHub Pages.

### Page Layouts
- `layout: workshop` — Overview/landing page (`index.md`)
- `layout: step` — Exercise pages with sidebar navigation (requires `step_number`, `permalink`)
- `layout: cheatsheet` — Walkthrough/reference pages (requires `parent_step`, `permalink`)

### Content Conventions
- Use GitHub callout syntax: `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`, `> [!IMPORTANT]`, `> [!CAUTION]`
- Use fenced code blocks with language identifiers (```python, ```bash, ```yaml)
- Steps are auto-discovered via `site.pages | where: "layout", "step" | sort: "step_number"`
- Cheatsheets are linked via `parent_step` matching a step's `step_number`

### Adding New Exercises
1. Create `workshop/exercises/exN_name/README.md` with front matter: `layout: step`, `step_number: N`, `permalink: /steps/N/`
2. Create `demo/demoN.md` with front matter: `layout: cheatsheet`, `parent_step: N`, `permalink: /cheatsheet/N/`
3. The sidebar navigation updates automatically
