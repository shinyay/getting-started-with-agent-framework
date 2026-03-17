---
layout: cheatsheet
title: "Exercise 2 — Walkthrough"
parent_step: 2
permalink: /cheatsheet/2/
---

# Demo 2 — Web Search Tool (Adding a Tool to Enable Web Search)

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python#using-built-in-and-hosted-tools
- https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-types/azure-ai-foundry-agent?pivots=programming-language-python
- https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.hostedwebsearchtool?view=agent-framework-python-latest
```

## Objectives

- Add **Hosted Web Search (a server-side search capability)** as a tool so the agent can perform web searches as needed and use the results as evidence for its answers
- Compared to Demo 1 (asking a model a question and getting an answer), Demo 2 **adds the ability to "search"**
- Additionally, provide steps to quickly avoid common pitfalls in production (Foundry Project endpoint / model deployment name / Bing connection / DNS / Dev Container env injection)


## Prerequisites
### 1) Demo 1 is Complete

(This assumes you have already logged in with Azure CLI and set up your Python environment.)

### 2) Setting Up Azure AI Foundry Agents (Recommended Backend for Demo 2 and Beyond)
Hosted Tools (such as Web Search) require native support on the service side.
This demo set recommends **Azure AI Foundry Agents**.

Required environment variables (both are mandatory):
```bash
export AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
export AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o-mini"
```

> Important: `AZURE_AI_PROJECT_ENDPOINT` is the **Foundry Project endpoint**.
> Example: `https://<account>.services.ai.azure.com/api/projects/<project-name-or-id>`
>
> An **Azure AI Services / Azure OpenAI endpoint** such as `https://<resource>.cognitiveservices.azure.com/` is a **different thing** and cannot be used for Demo 2 (it will return a 404 or fail to connect entirely).

> `AZURE_AI_MODEL_DEPLOYMENT_NAME` is the **deployment name shown under "Models + endpoints" in the Foundry project**.
> It is **not necessarily the same** as the Azure OpenAI deployment name from Demo 1 (this is the most common source of confusion).

> `AZURE_AI_PROJECT_ENDPOINT` can be obtained from the project details page in AI Foundry.

### 2.1) Bing Connection (Required for Hosted Web Search)
This demo uses **Hosted Web Search**. In Azure AI Foundry, Web Search is provided through a **Bing connection (Grounding)**, so the tool initialization will fail at runtime if the connection information is missing.

Set **one of the following** in your `.env` file.

#### A (Recommended): Grounding with Bing Search
- `BING_CONNECTION_ID` (alias: `BING_PROJECT_CONNECTION_ID`)

The value is the **project connection ID** of the Bing connection added to your Foundry project (e.g., a resource path like `/subscriptions/.../resourceGroups/.../providers/Microsoft.MachineLearningServices/workspaces/.../connections/...`).

How to obtain it (Foundry portal):
1. Open https://ai.azure.com/
2. From the top-right menu, go to **Operate** → left pane **Admin**
3. Select your project → **Add connection**
4. Choose **Grounding with Bing Search** as the Connection type and create the connection
5. Copy the **Project connection ID** from the **Connection details** of the created connection

(The official documentation uses the environment variable name `BING_PROJECT_CONNECTION_ID`, but the demo code in this repository also accepts `BING_CONNECTION_ID`.)

#### B: Bing Custom Search
- `BING_CUSTOM_CONNECTION_ID` (alias: `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID`)
- `BING_CUSTOM_INSTANCE_NAME` (alias: `BING_CUSTOM_SEARCH_INSTANCE_NAME`)

How to obtain: In the Foundry portal, create/add a Bing connection (Grounding or Custom Search) to your project, then copy the connection details (ID, etc.) and set them as environment variables.

### 2.2) Environment Variables Summary (Minimum Required)

| Category | Variable | Required | Notes |
|---|---|---:|---|
| Foundry | `AZURE_AI_PROJECT_ENDPOINT` | ✅ | `https://...services.ai.azure.com/api/projects/...` |
| Foundry | `AZURE_AI_MODEL_DEPLOYMENT_NAME` | ✅ | Deployment name from Foundry's **Models + endpoints** |
| Bing (A) | `BING_CONNECTION_ID` | ✅ (if using A) | Alias: `BING_PROJECT_CONNECTION_ID` |
| Bing (B) | `BING_CUSTOM_CONNECTION_ID` | ✅ (if using B) | Alias: `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID` |
| Bing (B) | `BING_CUSTOM_INSTANCE_NAME` | ✅ (if using B) | Alias: `BING_CUSTOM_SEARCH_INSTANCE_NAME` |

### 3) Additional Packages (If Not Already Installed)
```bash
pip install agent-framework-azure-ai --pre
```

> The Dev Container for this repository normally has the required packages installed via `requirements.txt`.
> (Manual installation is only necessary when running in a local environment, etc.)

### 4) Azure CLI Login
```bash
az login --use-device-code
```

> The subsequent demos connect using **Entra ID (Azure CLI) authentication** by default.

Login verification (optional):
```bash
az account show
```


## Steps

### Step 0. Prepare Your `.env` File (Recommended)
In Dev Container / Codespaces, `containerEnv` may cause environment variables to be **injected as empty strings**.
In that case, a typical `.env` loader (dotenv) determines that "the env var already exists" and **does not overwrite** it, leaving the value empty.

The `src/demo2_web_search.py` in this repository explicitly loads `.env` from the repository root
and **only fills in environment variables that are unset or empty**.

Create a `.env` file at the repository root (`/workspaces`) with at least the following (example):

```bash
AZURE_AI_PROJECT_ENDPOINT="https://<your-project>.services.ai.azure.com/api/projects/<project-id>"
AZURE_AI_MODEL_DEPLOYMENT_NAME="<your-foundry-model-deployment-name>"

# A: Grounding with Bing Search (Recommended)
BING_CONNECTION_ID="/subscriptions/.../resourceGroups/.../providers/Microsoft.MachineLearningServices/workspaces/.../connections/..."

# (If using B, use these instead of A)
# BING_CUSTOM_CONNECTION_ID="..."
# BING_CUSTOM_INSTANCE_NAME="..."
```

> Do **not commit** your `.env` file (it may contain secrets).

### Step 1. Review the Script (`src/demo2_web_search.py`)
This repository includes `src/demo2_web_search.py`.
The key points are as follows:

- Explicitly loads `.env` from the repository root (only fills in unset/empty values)
- Validates that `AZURE_AI_PROJECT_ENDPOINT` / `AZURE_AI_MODEL_DEPLOYMENT_NAME` are set
- Pre-checks whether the hostname of `AZURE_AI_PROJECT_ENDPOINT` can be resolved via DNS (surfaces DNS/Private Link issues early)
- Validates that a Bing connection is configured (`BING_CONNECTION_ID`, etc.)
- Uses `AzureAIAgentClient(...).as_agent(...)` to match API differences in Agent Framework

(This may differ from the `create_agent(...)` examples in the documentation, but **the code in this repository is authoritative**.)

### Step 2. Run
```bash
python3 src/demo2_web_search.py
```

### Step 3. Expected Output
If the environment is set up correctly, the script will complete without errors and print a response in the terminal in a format like the following:

- Suggests several venue candidates suitable for ~50 attendees on 2026/12/6 in Seattle
- A brief rationale for each candidate (location, approximate capacity, facilities, contact information, etc.)
- (Depending on the model/implementation) References web search results as supporting evidence

*Output content will vary from day to day (it depends on search results).*


## Technical Details (Key Points)

### 1) Tools Are "Extension Points That Expand the Model's Range of Actions"
  - The agent becomes capable of the "action" of **calling tools as needed → using the results as input to generate a response**


### 2) HostedWebSearchTool "Executes Web Searches on the Service Side"

- Rather than scraping locally, it calls a **Hosted Tool provided by the Foundry service**
- Therefore, whether the tool can be used depends on the **Foundry project settings (Bing connection, etc.)** and your account configuration (network, permissions)

### 3) Important: Tool Availability Depends on the Backend
The official documentation clearly states that **tool support varies by service provider**.
If things are not working, check the following:

Note (SDK API differences):
- The official documentation and sample code sometimes show `client.create_agent(...)` examples,
  but this repository uses `AzureAIAgentClient(...).as_agent(...)` to match the pinned version (`agent-framework==1.0.0b260123`).
  The purpose ("run an agent with a Web Search tool attached") is the same.


## Troubleshooting Checklist

### Exceptions to Check First
`src/demo2_web_search.py` is designed to detect configuration issues early and fail with clear messages.
Start by checking the exception message (especially "which env var is missing" or "whether DNS resolution failed").

### `AZURE_AI_PROJECT_ENDPOINT` is Not Set
```bash
echo $AZURE_AI_PROJECT_ENDPOINT
```
If empty, the variable has not been set.

#### Wrong Format (Got a 404 / Using a Different Service Endpoint)
`AZURE_AI_PROJECT_ENDPOINT` must be a **Foundry Project endpoint**.

- ✅ Example: `https://<account>.services.ai.azure.com/api/projects/<project-id>`
- ❌ Example: `https://<resource>.cognitiveservices.azure.com/` (Azure AI Services / Azure OpenAI endpoint)

### `Temporary failure in name resolution` / `Name or service not known` (DNS)
The hostname of `AZURE_AI_PROJECT_ENDPOINT` (e.g., `...services.ai.azure.com`) cannot be resolved via DNS from this execution environment.

Things to check:
- Ensure there are no copy errors in the value (re-copy from the Foundry Project overview)
- Check whether the Foundry project/account is configured with **Private networking / Private DNS**
    - If so, name resolution will not work from this Dev Container / Codespaces, and execution will fail
    - Either run from a network that can access the private DNS (e.g., corporate network / VPN), or try with a public project configuration

### `Hosted web search requires a Bing connection` (Missing Bing Connection)
Hosted Web Search requires a Bing connection.

- A (Recommended): `BING_CONNECTION_ID` (or `BING_PROJECT_CONNECTION_ID`)
- B: `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`

The value is not a "Bing API Key" but rather the **Project connection ID (resource path) of the connection added to the Foundry project**.

### `Failed to resolve model info for: ...` (Model Deployment Name Mismatch)
`AZURE_AI_MODEL_DEPLOYMENT_NAME` could not be resolved in the Foundry project.

Things to check:
- In Foundry portal → your project → **Models + endpoints**, verify that the deployment name exists
- Make sure you are not confusing it with the Azure OpenAI deployment name from Demo 1 (they are often **different**)

### Insufficient Permissions

The operation will fail if the executing user (the account logged in via `az login`) has insufficient permissions on the Foundry project.
Check the following with your team/administrator:

- Access rights to the target Foundry project (or the underlying workspace)
- Permission to use the Bing connection (Grounding)

(Error messages vary depending on the environment, so the best approach here is to "read the full error message first".)


## Next Demo
In Demo 3, we will add a **Hosted MCP Tool** and use Microsoft Learn MCP to enhance document references.
→ Open `demo3.md` to continue.
