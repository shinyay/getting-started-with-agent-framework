---
layout: step
title: "Setup & Installation"
step_number: 0
permalink: /setup/
---

## What You'll Need

Before starting the exercises, set up your development environment. The recommended approach is **Dev Container / GitHub Codespaces** — everything is pre-configured.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Azure subscription** | With permissions to create or access an Azure AI Foundry project |
| **Foundry project** | A deployed chat model (e.g. `gpt-4o-mini`) accessible via the project endpoint |
| **Bing Search connection** | Grounding with Bing Search connection configured in the Foundry project (required for Exercises 2, 4, 5, 6) |
| **Azure CLI** | Installed and authenticated — `az login` |
| **Dev Container / Codespaces** | Recommended runtime (Python 3.11+, all tooling pre-configured) |
| **Git & GitHub account** | To clone the repository |

---

## Step 1: Clone and Open in Dev Container

```bash
git clone https://github.com/shinyay/getting-started-with-agent-framework.git
cd getting-started-with-agent-framework
```

Then open in VS Code and select **"Reopen in Container"**, or launch via **GitHub Codespaces**.

> [!TIP]
> The Dev Container includes Python 3.11, Azure CLI, Node.js (for MCP), and all pip dependencies pre-installed.

---

## Step 2: Install Dependencies

Inside the Dev Container terminal:

```bash
pip install -r requirements.txt
```

> [!IMPORTANT]
> This repository locks Agent Framework to pre-release **`1.0.0b260123`** for reproducibility. Do **not** upgrade unless the workshop materials are updated accordingly.

---

## Step 3: Authenticate with Azure

```bash
az login --use-device-code
```

Verify the correct subscription is active:

```bash
az account show --query "{name:name, id:id}" -o table
```

---

## Step 4: Configure Environment Variables

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

> [!NOTE]
> **Fill-only `.env` pattern:** Scripts in this repository load `.env` explicitly and only fill environment variables that are **unset or empty**. Existing values (e.g. from Codespaces secrets) are never overwritten.

### Optional Variables (for Azure OpenAI entities)

These are only needed if you want to run the `entities/ai_genius_workflow/`:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | Chat model deployment name |
| `AZURE_OPENAI_API_KEY` | API key (if using key-based auth) |

---

## Step 5: Verify the Setup

Run Exercise 1's reference solution to confirm everything works:

```bash
python src/demo1_run_agent.py
```

✅ **Expected:** The agent responds to a built-in prompt. If you see a response, your environment is ready!

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `DefaultAzureCredential` or auth errors | Azure CLI session expired | Run `az login --use-device-code` |
| `DNS resolution failed` / timeout | Foundry endpoint unreachable | Check `AZURE_AI_PROJECT_ENDPOINT` value |
| `Model deployment not found` | Deployment name mismatch | Confirm `AZURE_AI_MODEL_DEPLOYMENT_NAME` in Foundry |
| Web search errors | Bing connection not configured | Set `BING_CONNECTION_ID` in `.env` |
| `npx: command not found` | Node.js missing | Use the Dev Container (includes Node.js) |
| Port 8080 in use (Exercise 6) | Another process on port | Set `DEVUI_PORT=<other-port>` in `.env` |
| `.env` values ignored | Codespaces empty-string vars | Scripts use fill-only pattern (fill unset/empty only) |

---

## Ready to Start!

Your environment is configured. Head to **[Exercise 1 →](../steps/1/)** to run your first agent!
