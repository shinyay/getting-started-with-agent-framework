---
layout: cheatsheet
title: "Exercise 3 — Walkthrough"
parent_step: 3
permalink: /cheatsheet/3/
---

# Demo 3 — MCP Stdio Tool (Launch sequential-thinking Locally)

Add an **stdio MCP server** as a tool and observe how the LLM uses the tool (sequential-thinking)
to build a plan step by step.

## Objectives
- Add `MCPStdioTool` to launch a **local MCP server (sequential-thinking)**
- Get a feel for **calling MCP (Model Context Protocol)-standardized tools from Foundry Agents**
- Visualize traces showing that an agent / tool was invoked using OTel spans (optional)

---

## Prerequisites
- Demo 2 is complete (Azure AI Foundry Agents env vars are configured)
- `agent-framework-azure-ai` is installed
- `az login` has been run

Additionally:
- `node` / `npx` must be available
  - These are normally pre-installed in this dev container

> This demo does not require adding a "Hosted tool" in the Foundry portal.
> `MCPStdioTool` launches `npx ...` locally.

> This demo runs with **Azure AI Foundry Agents** as the backend.
> `AZURE_AI_PROJECT_ENDPOINT` must be in the format `https://...services.ai.azure.com/api/projects/...` (Foundry Project endpoint).

---

## Steps

### Step 0. Verify `.env` (Recommended)
As with Demo 2, environment variables may be **injected as empty strings** in Dev Container / Codespaces.
The `src/demo3_hosted_mcp.py` script in this repository explicitly reads the `.env` file at the repository root and **fills in only unset or empty environment variables**.

At a minimum, make sure the following values are present:

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"
```

> Demo 3 does not use a Bing connection.

### Step 1. Review the Script (`src/demo3_hosted_mcp.py`)
This repository includes `src/demo3_hosted_mcp.py`.

Key points:
- Uses `AzureAIAgentClient(...).as_agent(...)` following the recommended Agent Framework pattern
- Tools:
  - `MCPStdioTool(name="sequential-thinking", command="npx", args=["-y", "@modelcontextprotocol/server-sequential-thinking"])`

Notes:
- Official / sample code may show examples using `client.create_agent(...)`, but the SDK version pinned in this repository uses `as_agent(...)` as the current API, so we follow that convention
- `npx` fetches the package on the first run, so it may take a little longer the first time

### Step 2. Run
```bash
python3 src/demo3_hosted_mcp.py
```

### Step 3. Expected Output
You should see an "event plan" output similar to the following:

- Progress logs for client/agent/run
- If a tool call occurs (and OTel is enabled), `[TOOL] ... tool=...` log entries
- Finally, a consolidated holiday party plan (venue options, timeline, role assignments, budget considerations, etc.)

---

## How to Verify MCP Is Working (Important)

### 1) Most Reliable: Check Run Traces in Foundry
The most reliable method is to confirm that **tool calls are recorded** in the Foundry-side traces.

### 2) Quick Check: OTel Span Logs (Optional)
When OpenTelemetry is available, this demo outputs a single-line summary for each agent/tool span.
If you see `[TOOL] ... tool=sequential-thinking`, it confirms that the tool was invoked.

---

## Technical Details (Understanding MCP / MCPStdioTool)

### 1) What Is MCP (Model Context Protocol)?
- A **standardized protocol** for when an LLM needs to use external tools or data sources
- In a nutshell:
  - **MCP Server**: Exposes tools (capabilities) and resources (data)
  - **MCP Client / Tool**: The agent side connects to and uses the server

### 2) What Are the Benefits of MCPStdioTool?
- Launches an MCP server **as a local process** and communicates via stdio
- Less dependent on adding tools or configuring connections in the Foundry portal, making it easier to reproduce locally

Caveats:
- Because it launches a local process, it depends on the execution environment's policies (whether external command execution is allowed)
- `npx -y ...` fetches external packages, so it may fail if there are network restrictions

### 3) sequential-thinking (Externalizing Step-by-Step Reasoning)
- Instead of having the model write an answer all at once, this pattern delegates the "thinking steps"
  to the tool and uses the results to compose the final answer — giving you hands-on experience with this approach

---

## Troubleshooting Checklist

### `npx` Not Found
- Install Node.js (normally not required in this dev container)

On Debian / Ubuntu-based environments, you can install it as follows:

```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

### `npx` Fails (Network Restrictions, etc.)
- Check whether the npm registry is reachable from your execution environment
- In environments that require a proxy, you may need to configure npm proxy settings

Additional Check (DNS):
- If the hostname in `AZURE_AI_PROJECT_ENDPOINT` (e.g., `*.services.ai.azure.com`) cannot be resolved via DNS from your execution environment, this demo will halt at startup
  - Example error: `Cannot resolve AZURE_AI_PROJECT_ENDPOINT host via DNS`
  - Resolution: Review your private networking / DNS configuration, or run from a network where DNS resolution is possible
  - As a temporary workaround, you can hard-code the address in `/etc/hosts`, but this is not recommended as a permanent solution since IP addresses may change

### "Tool Is Unavailable" Error
- Check whether local command execution is permitted (e.g., corporate device / CI restrictions)
- Check whether `npx` is starting successfully (look for errors in the logs above)

---

## Next Demo
In Demo 4, you will use `response_format` to extract **structured output**.
→ Open `demo4.md` to continue.
