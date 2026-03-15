# Exercise 3 — Integrate an MCP Stdio Tool

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 2 — Integration | ⭐⭐ Intermediate | 20–30 min |

## Learning Objectives

By the end of this exercise you will be able to:

1. Explain the **MCP (Model Context Protocol)** and how **stdio transport** works
2. Use `MCPStdioTool` to spawn a local MCP server process
3. Configure tool name, command, and args for an MCP stdio tool
4. Write agent instructions that guide the model to use the MCP tool

---

## Prerequisites

| Requirement | How to verify |
|-------------|--------------|
| Exercise 2 completed | You have a working web-search agent |
| Azure CLI logged in | `az account show` (should return your subscription) |
| `.env` configured | `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME` are set |
| Node.js + npx available | `npx --version` (the Dev Container has this pre-installed) |

---

## Background

### What Is MCP?

**Model Context Protocol (MCP)** is an open, standardized protocol for connecting AI models to external tools and data sources. Think of it as a universal adapter — any tool that speaks MCP can be used by any MCP-compatible agent framework.

MCP supports multiple **transports** (ways to communicate):

| Transport | How It Works | Use Case |
|-----------|-------------|----------|
| **stdio** | Spawns a local child process; communicates via stdin/stdout | Local tools, dev servers |
| **SSE / HTTP** | Connects to a remote HTTP server | Cloud-hosted tools |

In this exercise we use **stdio transport**: the agent framework spawns a local process (via `npx`) and talks to it over standard I/O.

### Key Difference: MCP Tools vs Hosted Tools

```
Hosted Tool (e.g., BingGroundingTool)       MCP Stdio Tool
─────────────────────────────────────       ──────────────────────────────
Runs on Azure AI Foundry service side       Runs locally as a child process
Configured via Foundry connections           Configured via command + args
No local dependencies needed                 Requires the tool binary (e.g., npx)
```

### The `sequential-thinking` MCP Server

The `@modelcontextprotocol/server-sequential-thinking` package provides a thinking tool that helps agents break complex problems into structured reasoning steps. When enabled, the agent can call this tool to decompose a task before generating its final answer.

> **Security note:** `MCPStdioTool` spawns a child process on your local machine. Only use MCP servers you trust. The `-y` flag tells `npx` to auto-install the package without prompting.

---

## Your Task

Open `starter.py` in this directory. You will find **5 TODO markers** — more work than Exercises 1–2, with less scaffolding. The helper functions (`.env` loading, DNS check, `_require_command`) are provided.

### Step 1 — Import `MCPStdioTool` (TODO 1)

At the top of the file, add the import for `MCPStdioTool`:

```python
from agent_framework import MCPStdioTool
```

This is the class that wraps an MCP server running over stdio transport.

### Step 2 — Verify `npx` Is Available (TODO 2)

Before creating the MCP tool, verify that `npx` exists on the system PATH:

```python
_require_command("npx")
```

The `_require_command()` helper (already provided) uses `shutil.which()` to check and raises a clear error if the command is missing.

### Step 3 — Create the MCP Stdio Tool (TODO 3)

Create an `MCPStdioTool` instance for the sequential-thinking server:

- **`name`** — `"sequential-thinking"` (identifies the tool to the agent)
- **`command`** — `"npx"` (the binary to spawn)
- **`args`** — `["-y", "@modelcontextprotocol/server-sequential-thinking"]`
- **`load_prompts`** — `False` (skip loading prompt templates from the server)

### Step 4 — Create the Agent with the MCP Tool (TODO 4)

Create an agent using `AzureAIAgentClient` and pass the MCP tool in the `tools=` list. Your agent instructions **must mention** the `sequential-thinking` tool — otherwise the model won't know to use it.

### Step 5 — Run the Agent and Print the Result (TODO 5)

Call `agent.run()` with a prompt and print `result.text`. The provided error-handling pattern for `ServiceResponseException` is included as a comment hint — use it to wrap the `agent.run()` call.

---

## Hints

Work through the hints progressively — try on your own first!

<details>
<summary>💡 Hint 1 — MCPStdioTool parameters</summary>

`MCPStdioTool` needs four parameters: `name`, `command`, `args` (as a list of strings), and `load_prompts` (a boolean).

```python
MCPStdioTool(
    name="...",
    command="...",
    args=[...],
    load_prompts=...,
)
```

</details>

<details>
<summary>💡 Hint 2 — Why load_prompts=False and the -y flag</summary>

- The `-y` flag tells `npx` to auto-install the package without interactive confirmation — essential for unattended execution.
- `load_prompts=False` skips loading prompt templates from the MCP server. The sequential-thinking server doesn't provide prompts, so this avoids unnecessary overhead.

The tool goes in the `tools=` list when creating the agent:

```python
client.as_agent(
    name="...",
    instructions="... use sequential-thinking ...",
    tools=[mcp_tool],
)
```

</details>

<details>
<summary>💡 Hint 3 — Near-complete solution</summary>

```python
_require_command("npx")

async with AzureCliCredential() as cred:
    async with AzureAIAgentClient(credential=cred) as client:
        async with client.as_agent(
            name="event_coordinator_specialist",
            instructions=(
                "You are the Event Coordinator Specialist, an expert in "
                "event planning and coordination. "
                "Use the sequential-thinking tool to break down the planning "
                "into clear steps before answering."
            ),
            tools=[
                MCPStdioTool(
                    name="sequential-thinking",
                    command="npx",
                    load_prompts=False,
                    args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
                )
            ],
        ) as agent:
            result = await agent.run(
                "Plan a corporate holiday party for 50 people "
                "on December 6th, 2026 in Seattle"
            )
            print("Result:\n")
            print(result.text)
```

</details>

---

## Validate Your Work

### 1. Run the check script (offline — no Azure needed)

```bash
bash workshop/exercises/ex3_mcp_tool/check.sh
```

This verifies syntax, required code patterns (MCPStdioTool, command/args, _require_command, as_agent with tools), and that all TODOs are resolved.

### 2. Run against Azure

```bash
python3 -u workshop/exercises/ex3_mcp_tool/starter.py
```

**Expected behaviour:**

- The script verifies `npx` is available, then connects to your Foundry project.
- An MCP stdio process is spawned for `sequential-thinking`.
- The agent uses the thinking tool to plan, then generates a structured party-planning response.
- You see `Result:` followed by the agent's text output.
- If OpenTelemetry is available, `[TOOL]` span lines appear showing the MCP tool invocation.

---

## Bonus Challenges

1. **Try a different MCP server** — Replace `@modelcontextprotocol/server-sequential-thinking` with another MCP-compatible server (e.g., a filesystem or git server). Update the tool name and instructions accordingly.
2. **Add error handling for npx failures** — What happens if the MCP server fails to start? Wrap the agent creation in a try/except and provide a helpful error message.
3. **Combine with web search** — Create an agent with both an MCP tool and a hosted tool (like `BingGroundingTool` from Exercise 2). How do you pass multiple tools?

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `RuntimeError: Required command is not available on PATH: npx` | Node.js / npx not installed | Install Node.js or use the Dev Container (which has it pre-installed) |
| `npm ERR! code E404` or network timeout during npx | npm registry not reachable | Check your network connection; corporate proxies may block npm |
| Agent responds but doesn't use `sequential-thinking` | Instructions don't mention the tool | Your agent instructions **must** tell the model to use the tool by name |
| `Cannot resolve ... host via DNS` | Foundry project uses private networking | Use a public endpoint or run from a network that can resolve the private DNS |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` error | Deployment name mismatch | Check the Foundry portal → Models + endpoints → confirm the deployment name |
| `RuntimeError: Required environment variable ...` | Missing or empty env var | Check `.env` at the repo root — ensure values are not empty strings |
| `ModuleNotFoundError: agent_framework` | Dependencies not installed | Run `pip install -r requirements.txt` |

---

## Solution Reference

See the complete working solution at: **`src/demo3_hosted_mcp.py`**
