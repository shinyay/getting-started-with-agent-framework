---
layout: workshop
---

## 🎓 Workshop Overview

A progressive **7-exercise workshop** for building AI agents and multi-agent workflows with **Microsoft Agent Framework** in Python. From creating your first agent to designing multi-agent pipelines with streaming events — all powered by **Azure AI Foundry**.

## How to Use This Workshop

1. **[Complete the Setup](setup/)** — Install prerequisites, configure Dev Container, set up Azure credentials
2. **Click an exercise in the sidebar** (or the curriculum table below)
3. **Open your terminal** alongside this site — each exercise tells you exactly what to code
4. **Use the 📋 Walkthrough** links for conceptual guidance without seeing the full solution
5. **Track your progress** with the sidebar progress bar

> [!TIP]
> Each exercise has a `starter.py` with `# TODO:` markers. Fill in the blanks, then run `check.sh` to validate. Reference solutions are in `src/demo*.py` if you get stuck.

---

## Skill Progression

```
Exercise 1   Exercise 2    Exercise 3     Exercise 4      Exercise 5       Exercise 6      Exercise 7
Run Agent → Web Search → MCP Tool → Struct Output → Multi-Agent → DevUI → Capstone
    ⭐          ⭐          ⭐⭐          ⭐⭐          ⭐⭐⭐        ⭐⭐⭐       ⭐⭐⭐⭐
 create      add hosted   MCP stdio     Pydantic       workflow       visual       design your
 & run       web search   tool via      + response_    edges +        debugger     own agent
 agent       tool         npx           format         streaming      + API
```

| Phase | Exercises | Scaffolding Level | What you do |
|-------|-----------|-------------------|-------------|
| 🟢 **Foundations** | 1, 2 | High — fill-in-the-blank | Complete `TODO` markers in mostly-written code |
| 🟡 **Integration** | 3, 4 | Medium — guided | Implement key functions with hints and references |
| 🟠 **Orchestration** | 5, 6 | Low — goal-oriented | Build toward a described outcome with minimal starter code |
| 🔴 **Capstone** | 7 | None — from scratch | Design and implement your own agent end-to-end |

---

## Curriculum

| # | Title | Key Concepts | Difficulty | Time |
|:-:|-------|-------------|:----------:|------|
| [**Setup**](setup/) | Setup & Installation | Dev Container, Azure CLI, environment variables | — | 15-30 min |
| [**1**](steps/1/) | Run Your First Agent | `AzureAIAgentClient`, `.as_agent()`, `run()`, async lifecycle | ⭐ | 15-20 min |
| [**2**](steps/2/) | Web Search Tool | `HostedWebSearchTool`, Bing grounding, tool integration | ⭐ | 20-30 min |
| [**3**](steps/3/) | MCP Stdio Tool | Model Context Protocol, `MCPStdioTool`, local tool servers | ⭐⭐ | 20-30 min |
| [**4**](steps/4/) | Structured Output | `response_format`, Pydantic `BaseModel`, output parsing | ⭐⭐ | 20-25 min |
| [**5**](steps/5/) | Multi-Agent Workflow | Workflow orchestration, agent edges, streaming events | ⭐⭐⭐ | 30-40 min |
| [**6**](steps/6/) | DevUI | DevUI server, entity discovery, OpenAI-compatible API | ⭐⭐⭐ | 25-35 min |
| [**7**](steps/7/) | Capstone Project | All prior concepts — build your own agent or workflow | ⭐⭐⭐⭐ | 45+ min |

**Total: 7 exercises across 4 phases — estimated ~5 hours**

---

## What is Microsoft Agent Framework?

**Microsoft Agent Framework** is a Python SDK for building AI agents backed by **Azure AI Foundry**. It provides a structured way to create agents that can use tools, produce structured output, and orchestrate multi-agent workflows — all with streaming support and a visual debugging UI.

### Key Features

- 🤖 **Agent Creation** — `AzureAIAgentClient` → `.as_agent()` → `run()` lifecycle
- 🔍 **Tool Integration** — Hosted tools (Web Search) and local tools (MCP stdio)
- 📊 **Structured Output** — Pydantic models with `response_format` parameter
- 🔄 **Workflow Orchestration** — Multi-agent pipelines with `WorkflowBuilder` and edges
- 📺 **DevUI** — Visual debugger with OpenAI-compatible API endpoint
- 🔐 **Azure-native** — Entra ID authentication, Foundry project integration

---

## Quick Start

```bash
# 1. Clone and open in Dev Container / Codespaces
git clone https://github.com/shinyay/getting-started-with-agent-framework.git
cd getting-started-with-agent-framework
# Open in VS Code → "Reopen in Container"

# 2. Configure environment
cp .env.example .env
# Edit .env with your Azure AI Foundry values

# 3. Authenticate
az login --use-device-code

# 4. Verify setup — run Exercise 1's solution
python src/demo1_run_agent.py
```

For detailed setup, see the **[Setup & Installation](setup/)** page.

---

## Exercise Structure

Each exercise directory (`workshop/exercises/ex<N>_*/`) contains:

| File | Purpose |
|------|---------|
| `README.md` | Objectives, concepts, step-by-step instructions |
| `starter.py` | Skeleton code with `# TODO:` markers |
| `check.sh` | Validation script to verify your solution |

Solutions are in `src/demo*.py`. Detailed walkthroughs are available as 📋 links in the sidebar.

---

## Requirements

- **Azure subscription** with AI Foundry project access
- **Python 3.10+** (3.11+ recommended)
- **Azure CLI** installed and authenticated
- **Node.js / npx** (for MCP exercises)
- **VS Code** with Dev Container support (recommended)

> ⚠️ **Version note:** This workshop targets Agent Framework **`1.0.0b260123`** (pre-release). Online documentation may describe a newer version with API differences. When in doubt, trust the code in this repository.

👉 **[Start the Setup →](setup/)**
