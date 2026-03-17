---
layout: cheatsheet
title: "Exercise 1 — Walkthrough"
parent_step: 1
permalink: /cheatsheet/1/
---

# Demo 1 — Getting Started (Create and Run Your First Foundry Agent)

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
```

## Objectives (What You Will Learn in This Demo)
- **Create and run a single agent** using Agent Framework (Python)
- Use Azure AI Foundry Agents (`AzureAIAgentClient`) as the backend and retrieve the result of `agent.run()`
- Experience the minimal unit of an agent: "Agent = LLM + Instructions + Execution API"

Note:
- Demos 2/3/5 that follow build on the same backend (Foundry Agents)
- Direct Azure OpenAI connection (`AzureOpenAIChatClient`) is a separate backend (covered in Demos 4/6 in this repository)

---

## Prerequisites (Once These Are in Place, the Rest Is Just Copy-and-Paste)
### A. Execution Environment
- **Dev Containers / GitHub Codespaces** (recommended)
  - For Codespaces: just open the repository and click **"Create codespace"**
  - For local Dev Containers: use "Reopen in Container" in VS Code

> Even without Dev Containers, you can run the demo as long as you have Python 3.10+ and `pip`.

### B. Setting Up Azure AI Foundry Agents (One-Time Setup)
This Demo 1 uses **Azure AI Foundry Project** as its backend.

1. Prepare a Hub / Project in Azure AI Foundry (an existing one is fine)
2. Deploy a model under the Project's **Models + endpoints** (e.g., `gpt-4o-mini`)
3. Grant RBAC permissions to the executing user (the account used for `az login`) so they can run Agents on the Project / Hub

The two main things you need for this demo are:
- **Project endpoint** (`AZURE_AI_PROJECT_ENDPOINT`)
- **Model deployment name** (`AZURE_AI_MODEL_DEPLOYMENT_NAME`)

### C. Required Environment Variables (Set Using One of the Following Methods)
- Method 1: Codespaces **Secrets** (recommended — prevents key leakage)
- Method 2: Use `export` inside the Dev Container
- Method 3: `.env` (do NOT commit this file; provide a `.env.example` instead)

Minimum required:
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

Example:
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<account>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

Common Pitfalls:
- `AZURE_AI_PROJECT_ENDPOINT` must be the **Foundry Project endpoint** (`https://...services.ai.azure.com/api/projects/...`).
  - This is different from the Azure OpenAI or Azure AI Services endpoint (`...cognitiveservices.azure.com`)
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` is the **deployment name on the Foundry project side** (not the model name)

---

## Steps (Step-by-step)

### Step 1. Install Dependencies
If you are using a Dev Container, the dependencies are most likely already installed. If not, run the following:

```bash
pip install agent-framework-azure-ai --pre
```

### Step 2. Log In with Azure CLI (Entra ID Authentication)
Run this **inside Codespaces / the container**.

```bash
az login
```

> In Codespaces, you may not be able to open a browser, so `--use-device-code` is convenient.
> `az login --use-device-code`

#### Authentication Method Used in This Demo (Important)
This demo uses **Microsoft Entra ID (= Azure CLI credential)**.
Therefore, `az login` is required.

### Step 3. Review the Script (`src/demo1_run_agent.py`)
This repository includes `src/demo1_run_agent.py`.
(You do not need to create it manually.)

(Note)
- The official documentation may show examples using `create_agent(...)`,
  but this repository uses `as_agent(...)` to match the pinned version (`agent-framework==1.0.0b260123`).

#### Workarounds for Common Pitfalls Included in This Repository
- In Dev Container / Codespaces environments, environment variables may be injected as **empty strings**.
  In that case, a typical dotenv load will fail to populate the values properly.
- To address this, `src/demo1_run_agent.py` **explicitly loads the `.env` file from the repository root and only fills in environment variables that are unset or empty**.

### Step 4. Run
```bash
python3 -u src/demo1_run_agent.py
```

Expected behavior:
- `venue_specialist` proposes an event plan (venue, candidates, key points, etc.)
- `result.text` is displayed without errors

---

## Technical Details (What Happens Behind the Scenes in This Demo)

### 1) Architecture Overview (Foundry / Local Code)
At a high level, this demo consists of the following three layers:

1. **Azure AI Foundry side**
  - Project (Hub/Project)
  - Model deployment under Models + endpoints
2. **Environment variables (`.env` / Secrets / export)**
  - `AZURE_AI_PROJECT_ENDPOINT`
  - `AZURE_AI_MODEL_DEPLOYMENT_NAME`
  - Authentication credentials (Entra ID: `az login`)
3. **Application code (`src/demo1_run_agent.py`)**
  - Creates an `AzureAIAgentClient`, converts it to an Agent with `as_agent()`, and calls `run()`

### 2) `AzureAIAgentClient` Is a Client That Connects to Foundry Agents
`AzureAIAgentClient` is the client used to connect to and execute Agents on an Azure AI Foundry Project.
In this demo, the Project and Model are specified via environment variables, and `agent.run()` is called at runtime.

### 3) Observability (OpenTelemetry / OTel)
If OpenTelemetry is installed in the environment, the demo script
displays Agent execution and Tool invocations as **short one-line log entries** (for observability during the demo).

### 4) `run()` Is a Single-Turn Execution
`run()` performs a single inference for a single input (user utterance) and returns the result as a `ChatResponse`.
`result.text` is the final result in human-readable text form.

#### Reference: Streaming Version (`run_stream()`)
As described in the Learn tutorials, you can use `run_stream()` if you want streaming output:

```python
async def main():
  async for update in agent.run_stream("Tell me a joke about a pirate."):
    if update.text:
      print(update.text, end="", flush=True)
  print()
```

---

## Troubleshooting

### Common Issue 1: Authentication Error (401/403)
- Verify that `az login` was successful inside the container
- Verify that the appropriate role has been assigned on the target Azure OpenAI resource
- If the subscription is different, align it with `az account set`

### Common Issue 2: `AZURE_AI_PROJECT_ENDPOINT` Is Incorrect / 404
`AZURE_AI_PROJECT_ENDPOINT` must be the **Foundry Project endpoint**.

- ✅ Example: `https://<account>.services.ai.azure.com/api/projects/<project-id>`
- ❌ Example: `https://<resource>.cognitiveservices.azure.com/` (Azure OpenAI / Azure AI Services endpoint)

### Common Issue 3: `Failed to resolve model info` (Wrong Deployment Name)
`AZURE_AI_MODEL_DEPLOYMENT_NAME` cannot be resolved in the Foundry project.

Check:
- Foundry portal → target project → verify the deployment name exists under **Models + endpoints**

### Common Issue 4: DNS Resolution Fails and the Process Stalls Before Starting
The host in `AZURE_AI_PROJECT_ENDPOINT` cannot be resolved via DNS from this execution environment.

- Resolution: Review your private networking / private DNS configuration, or run from a network where DNS resolution is available

---

## Next Demo
In Demo 2, we will add a **tool (Hosted Web Search)** to the agent.
→ Open `demo2.md` to continue.
