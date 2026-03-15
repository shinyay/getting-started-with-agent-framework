# Microsoft Agent Framework Hands-On Workshop

> **Format:** Hybrid — instructor-led concept introductions followed by self-paced exercises  
> **Duration:** ≈ 5 hours (including breaks)  
> **Level:** Experienced developers new to Microsoft Agent Framework / Azure AI

---

## What You'll Learn

By the end of this workshop you will be able to:

- Create and run an AI agent backed by Azure AI Foundry using **Microsoft Agent Framework**
- Integrate external capabilities — **Web Search**, **MCP tools**, and **structured output** — into agents
- Orchestrate **multi-agent workflows** with edge-based routing and streaming
- Launch the **DevUI** visual debugger to inspect agent behaviour in real time
- Design and build your own agent from scratch

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Azure subscription** | With permissions to create or access an Azure AI Foundry project |
| **Foundry project** | A deployed chat model (e.g. `gpt-4o-mini`) accessible via the project endpoint |
| **Bing Search connection** | Grounding with Bing Search connection configured in the Foundry project (required for Exercises 2, 4, 5, 6) |
| **Azure CLI** | Installed and authenticated — `az login` (use `az login --use-device-code` in headless environments) |
| **Dev Container / Codespaces** | Recommended runtime environment (Python 3.11+, all tooling pre-configured) |
| **Git & GitHub account** | To clone the repository |

---

## Environment Setup

### 1. Clone and open in Dev Container

```bash
git clone <this-repository-url>
# Open in VS Code → "Reopen in Container", or launch via GitHub Codespaces
```

### 2. Install dependencies

Inside the Dev Container terminal:

```bash
pip install -r requirements.txt
```

> **Pinned version:** This repository locks Agent Framework to pre-release `1.0.0b260123` for reproducibility.  
> Do **not** upgrade unless the workshop materials are updated accordingly.

### 3. Authenticate with Azure

```bash
az login --use-device-code
```

Verify the correct subscription is active:

```bash
az account show --query "{name:name, id:id}" -o table
```

### 4. Configure environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with the required variables:

| Variable | Required | Description |
|----------|:--------:|-------------|
| `AZURE_AI_PROJECT_ENDPOINT` | ✅ | Foundry project endpoint (e.g. `https://<account>.services.ai.azure.com/api/projects/<project-id>`) |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | ✅ | Model deployment name from Foundry → Models + endpoints (e.g. `gpt-4o-mini`) |
| `BING_CONNECTION_ID` | ✅ (Ex 2+) | Grounding with Bing Search connection ID from the Foundry project |

> **Fill-only `.env` pattern:** Scripts in this repository load `.env` explicitly and only fill environment variables that are **unset or empty**. Existing values (e.g. from Codespaces secrets) are never overwritten. This avoids surprises when Dev Containers inject empty-string env vars.

### 5. Verify the setup

Run Exercise 1's solution to confirm everything works:

```bash
python src/demo1_run_agent.py
```

✅ **Expected:** The agent responds to a built-in prompt. If you see a response, your environment is ready.

---

## Workshop Agenda

| Block | Duration | Content |
|-------|:--------:|---------|
| **Intro & Setup** | 30 min | Workshop overview, architecture concepts, environment verification |
| **Phase 1 — Foundations** | 60 min | Exercise 1: Run Agent · Exercise 2: Web Search Tool |
| ☕ Break | 15 min | |
| **Phase 2 — Integration** | 60 min | Exercise 3: MCP Tool · Exercise 4: Structured Output |
| ☕ Break | 15 min | |
| **Phase 3 — Orchestration** | 60 min | Exercise 5: Multi-Agent Workflow · Exercise 6: DevUI |
| **Phase 4 — Capstone** | 45 min | Exercise 7: Build Your Own Agent |
| **Wrap-up & Q&A** | 15 min | Review, next steps, additional resources |

**Total: ≈ 5 hours**

---

## How to Work Through Exercises

### Progressive scaffolding

The exercises are designed with **increasing autonomy**:

| Phase | Scaffolding Level | What you do |
|-------|-------------------|-------------|
| **Phase 1** (Foundations) | High — fill-in-the-blank | Complete `TODO` markers in mostly-written code |
| **Phase 2** (Integration) | Medium — guided implementation | Implement key functions with hints and references |
| **Phase 3** (Orchestration) | Low — goal-oriented | Build toward a described outcome with minimal starter code |
| **Phase 4** (Capstone) | None — from scratch | Design and implement your own agent end-to-end |

### Exercise structure

Each exercise directory (`workshop/exercises/ex<N>_*/`) contains:

| File | Purpose |
|------|---------|
| `README.md` | Objectives, concepts, step-by-step instructions |
| `starter.py` | Skeleton code with `# TODO:` markers for you to complete |
| `check.sh` | Validation script — run after completing the exercise to verify correctness |

### Finding solutions

If you get stuck, the working implementations are in the `src/` directory:

```
src/demo1_run_agent.py          ← Solution for Exercise 1
src/demo2_web_search.py         ← Solution for Exercise 2
src/demo3_hosted_mcp.py         ← Solution for Exercise 3
src/demo4_structured_output.py  ← Solution for Exercise 4
src/demo5_workflow_edges.py      ← Solution for Exercise 5
src/demo6_devui.py              ← Solution for Exercise 6
```

> **Tip:** Try to solve each exercise on your own before looking at the solution. The `demo/*.md` files provide detailed walkthroughs if you need conceptual guidance without seeing the full code.

---

## Exercise Overview

| # | Title | What You Build | Key Concepts | Difficulty |
|:-:|-------|----------------|--------------|:----------:|
| 1 | **Run Agent** | A basic Foundry-backed agent that answers a question | `AzureAIAgentClient`, `as_agent()`, `run()`, async lifecycle | ⭐ |
| 2 | **Web Search Tool** | An agent augmented with live web search | Hosted Web Search tool, Bing grounding connection, tool integration | ⭐ |
| 3 | **MCP Tool** | An agent that uses an MCP stdio tool via `npx` | Model Context Protocol, `MCPStdioTool`, local tool servers | ⭐⭐ |
| 4 | **Structured Output** | An agent that returns validated Pydantic models | `response_format`, Pydantic `BaseModel`, output parsing, fallback strategies | ⭐⭐ |
| 5 | **Multi-Agent Workflow** | A pipeline of specialised agents connected by edges | Workflow orchestration, agent edges, streaming events, `run_stream()` | ⭐⭐⭐ |
| 6 | **DevUI** | A visual debugger serving agents over an OpenAI-compatible API | DevUI server, port configuration, entity-based workflows, health checks | ⭐⭐⭐ |
| 7 | **Build Your Own** | Your custom agent or workflow (capstone) | All prior concepts — applied to a problem of your choice | ⭐⭐⭐⭐ |

---

## Supplementary Materials

The `workshop/reference/` directory contains additional materials to support your learning:

- **Concept cheat-sheets** — quick-reference cards for Agent Framework APIs
- **Architecture diagrams** — visual overviews of agent lifecycle and workflow patterns
- **Further reading links** — curated pointers to Microsoft Learn docs and samples

Also see the supplementary guides in the repository root:

| File | Content |
|------|---------|
| `demo/guide-demo.md` | Learning guide mapping demos to key Agent Framework concepts |
| `demo/guide-tech.md` | Technical reference guide for deeper understanding |

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `DefaultAzureCredential` or auth errors | Azure CLI session expired or wrong subscription | Run `az login --use-device-code` and verify with `az account show` |
| `DNS resolution failed` / connection timeout | Foundry endpoint unreachable (private networking or typo) | Check `AZURE_AI_PROJECT_ENDPOINT` value; verify network access to `*.services.ai.azure.com` |
| `Model deployment not found` | Deployment name mismatch | Confirm `AZURE_AI_MODEL_DEPLOYMENT_NAME` matches Foundry → Models + endpoints exactly |
| Web search returns no results / errors | Bing connection not configured | Set `BING_CONNECTION_ID` in `.env`; verify the Grounding with Bing Search connection in Foundry project |
| `npx: command not found` (Exercise 3) | Node.js / npm not installed in the environment | Use the Dev Container (includes Node.js); or install Node.js manually |
| MCP tool timeout | Network restriction blocking npm registry | Check proxy/firewall settings; pre-install the MCP package if needed |
| Port 8080 already in use (Exercise 6) | Another process occupies the DevUI port | Set `DEVUI_PORT=<other-port>` in `.env`, or stop the conflicting process |
| Empty or `None` structured output (Exercise 4) | Model returned data in unexpected format | Check the fallback path — parse `response.text` if `response.value` is empty (see solution code) |
| `.env` values ignored | Codespaces injected empty-string env vars that take precedence | Ensure scripts use the fill-only pattern (load `.env`, fill only unset/empty vars) |

---

## Solutions

Each exercise maps directly to a working reference solution:

| Exercise | Solution File | Walkthrough |
|:--------:|---------------|-------------|
| 1 | `src/demo1_run_agent.py` | `demo/demo1.md` |
| 2 | `src/demo2_web_search.py` | `demo/demo2.md` |
| 3 | `src/demo3_hosted_mcp.py` | `demo/demo3.md` |
| 4 | `src/demo4_structured_output.py` | `demo/demo4.md` |
| 5 | `src/demo5_workflow_edges.py` | `demo/demo5.md` |
| 6 | `src/demo6_devui.py` | `demo/demo6.md` |
| 7 | *(your own creation)* | — |

> **Remember:** Exercise 7 is a capstone — there is no single "correct" solution. Use any combination of the patterns from Exercises 1–6 to build something meaningful to you.

---

## Additional Resources

- [Microsoft Agent Framework — PyPI](https://pypi.org/project/agent-framework/)
- [Azure AI Foundry documentation — Microsoft Learn](https://learn.microsoft.com/azure/ai-studio/)
- [Model Context Protocol (MCP) specification](https://modelcontextprotocol.io/)

> ⚠️ **Version note:** This workshop targets Agent Framework **`1.0.0b260123`** (pre-release). Online documentation may describe a newer version with API differences. When in doubt, trust the code in this repository.
