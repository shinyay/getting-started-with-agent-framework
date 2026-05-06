# Setting up an Azure Foundry environment for the demos

> **Last validated**: May 6, 2026 (against `agent-framework-foundry==1.2.2`)
> **Validated region**: East US 2
> **Total cost during validation**: ~$0.50
> **All 7 demos PASSED end-to-end** with this exact setup

This guide walks you through provisioning the **Azure-side** environment that the workshop demos talk to. The repo's other setup file ([`setup.md`](../setup.md)) covers the **local** Dev Container / Codespaces side; this one covers what you need in your Azure subscription before any demo can run.

---

## Table of contents

- [TL;DR — Quick start (5 commands)](#tldr--quick-start-5-commands)
- [What this guide provisions](#what-this-guide-provisions)
- [Prerequisites](#prerequisites)
- [Step 0 — Sign in and pick a region](#step-0--sign-in-and-pick-a-region)
- [Step 1 — Create a Foundry account (AIServices)](#step-1--create-a-foundry-account-aiservices)
- [Step 2 — Create a Foundry project](#step-2--create-a-foundry-project)
- [Step 3 — Deploy a chat model (`gpt-4.1-mini`)](#step-3--deploy-a-chat-model-gpt-41-mini)
- [Step 4 — Provision Grounding with Bing Search](#step-4--provision-grounding-with-bing-search)
- [Step 5 — Wire Bing as a Foundry project connection](#step-5--wire-bing-as-a-foundry-project-connection)
- [Step 6 — (Optional) Separate Azure OpenAI for Demo 6](#step-6--optional-separate-azure-openai-for-demo-6)
- [Step 7 — Capture endpoints + keys](#step-7--capture-endpoints--keys)
- [Configure your `.env`](#configure-your-env)
- [Smoke test the demos](#smoke-test-the-demos)
- [Troubleshooting](#troubleshooting)
- [Cleanup / teardown](#cleanup--teardown)
- [Cost reference](#cost-reference)
- [What this guide does NOT cover](#what-this-guide-does-not-cover)

---

## TL;DR — Quick start (5 commands)

> For experienced Azure users with `az login` already done. Replace placeholders with your own values.

```bash
# 0. Variables (substitute your own)
SUB="$(az account show --query id -o tsv)"
RG="rg-foundry-demos"
ACCT="foundry-demos-$RANDOM"
PROJ="${ACCT}-project"
LOC="eastus2"

# 1. Foundry account + project
az group create -n "$RG" -l "$LOC"
az cognitiveservices account create -n "$ACCT" -g "$RG" --kind AIServices --sku S0 \
  --location "$LOC" --custom-domain "$ACCT" --yes
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ?api-version=2025-04-01-preview" \
  --body '{"location":"'"$LOC"'","identity":{"type":"SystemAssigned"},"properties":{}}'

# 2. Deploy gpt-4.1-mini (Standard, 30 K TPM)
az cognitiveservices account deployment create -n "$ACCT" -g "$RG" \
  --deployment-name gpt-4-1-mini --model-name gpt-4.1-mini --model-version 2025-04-14 \
  --model-format OpenAI --sku-name Standard --sku-capacity 30

# 3. Bing Grounding resource
az resource create -g "$RG" -n "bing-grounding-$RANDOM" \
  --resource-type Microsoft.Bing/accounts --location global --is-full-object \
  --properties '{"location":"global","sku":{"name":"G1"},"kind":"Bing.Grounding"}'

# 4–5. Get Bing key + register as Foundry connection (see Step 5 for the full PUT body)
# 6. Capture endpoints/keys → .env (see "Configure your .env" below)
```

That's the **happy path**. The rest of this guide explains each step, the gotchas, and how to clean up.

---

## What this guide provisions

```text
┌───────────────────────────────────────────────────────────────────────┐
│  Resource group  (e.g. rg-foundry-demos)                              │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Microsoft.CognitiveServices/accounts                         │   │
│  │  (kind=AIServices — the Foundry account)                     │   │
│  │                                                               │   │
│  │  └─ /projects/<your-project>                                 │   │
│  │       ├─ deployment: gpt-4-1-mini  ← Demos 1, 2, 3, 4, 5     │   │
│  │       └─ connection: bing-conn      ← Demos 2, 4, 5           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Microsoft.Bing/accounts                                      │   │
│  │  (kind=Bing.Grounding, SKU G1)                               │   │
│  │  → backs the Foundry connection above                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Microsoft.CognitiveServices/accounts                         │   │
│  │  (kind=OpenAI, separate AOAI account — only for Demo 6)      │   │
│  │  └─ deployment: gpt-4-1-mini                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Cost summary (validated May 6, 2026)

| Resource | SKU | Idle/hour | Per-call |
|----------|-----|----------:|---------:|
| Foundry account (`AIServices`) | S0 | $0 | — |
| `gpt-4-1-mini` deployment in Foundry | Standard, 30 K TPM | $0 | ~$0.0002 / 1K tokens |
| Bing.Grounding | G1 | $0 | ~$0.025 / query |
| AOAI account (`OpenAI`) | S0 | $0 | — |
| `gpt-4-1-mini` deployment in AOAI | Standard, 30 K TPM | $0 | ~$0.0002 / 1K tokens |
| **Full smoke pass — all 7 demos** | | | **~$0.50** |

Idle costs are zero — you only pay per LLM token + per Bing query. See [Cost reference](#cost-reference) for actuals.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Azure subscription with **Contributor** at the resource-group scope | Tenant policy must allow `Microsoft.Bing/accounts` and `Microsoft.CognitiveServices/accounts` |
| `az` CLI **2.50+** | Check: `az --version` |
| Python 3.10+ | Dev Container uses 3.11 |
| One of **East US 2**, **Sweden Central**, or **Australia East** | Verified to have all needed resource types in May 2026 |
| `az login` completed | This guide assumes `az account show` works |

> [!TIP]
> If you're not sure your subscription supports these, verify first (read-only):
> ```bash
> az provider show -n Microsoft.Bing --query registrationState -o tsv               # → Registered
> az provider show -n Microsoft.CognitiveServices --query registrationState -o tsv  # → Registered
> ```

> [!WARNING] Foundry terminology
> - **Foundry account** = `Microsoft.CognitiveServices/accounts` with `kind=AIServices`
> - **Foundry project** = `Microsoft.CognitiveServices/accounts/projects` (child resource)
> - **Foundry connection** = a project-scoped pointer to an external resource (Bing, AOAI, etc.)

---

## Step 0 — Sign in and pick a region

```bash
az login
az account set --subscription "<your-subscription-id>"
az account show --query "{user:user.name, sub:name, tenant:tenantDisplayName}" -o table
```

Set shell variables you'll reuse below:

```bash
export SUB="$(az account show --query id -o tsv)"
export RG="rg-foundry-demos"
export LOC="eastus2"
export ACCT="foundry-demos-$RANDOM"        # globally unique
export PROJ="${ACCT}-project"
export BING_RES="bing-grounding-$RANDOM"   # globally unique
export AOAI_ACCT="aoai-demos-$RANDOM"      # globally unique
```

> [!NOTE] Portal alternative
> Sign in at <https://portal.azure.com>. Region/subscription pickers are top-right.

---

## Step 1 — Create a Foundry account (AIServices)

A Foundry account is a Cognitive Services resource with `kind=AIServices`.

```bash
az group create -n "$RG" -l "$LOC"

az cognitiveservices account create \
  --name "$ACCT" \
  --resource-group "$RG" \
  --kind AIServices \
  --sku S0 \
  --location "$LOC" \
  --custom-domain "$ACCT" \
  --yes \
  --tags workshop=agent-framework
```

Key flags:
- `--kind AIServices` — what makes it a Foundry account
- `--custom-domain` — required for project endpoints (`https://<acct>.services.ai.azure.com`)
- `--sku S0` — Standard tier (only paid SKU; pay-per-call)

Verify:
```bash
az cognitiveservices account show -n "$ACCT" -g "$RG" \
  --query "{name:name, kind:kind, state:properties.provisioningState, endpoint:properties.endpoint}" -o table
```

> [!NOTE] Portal alternative
> Azure Portal → **Azure AI Foundry** → **+ Create** → choose subscription/RG/region/name → review + create.

---

## Step 2 — Create a Foundry project

Foundry projects are child resources under the AIServices account. The CLI's `cognitiveservices` group doesn't model them, so use `az rest`:

```bash
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ?api-version=2025-04-01-preview" \
  --body '{
    "location": "'"$LOC"'",
    "identity": {"type": "SystemAssigned"},
    "properties": {}
  }'
```

Verify and capture the project endpoint:

```bash
az rest --method GET \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects?api-version=2025-04-01-preview" \
  --query "value[].{name:name, state:properties.provisioningState, endpoint:properties.endpoints}" -o json
```

The response includes the **AI Foundry API endpoint**, which looks like:
```
https://<acct>.services.ai.azure.com/api/projects/<project>
```

Save it — this is your **`FOUNDRY_PROJECT_ENDPOINT`**.

> [!NOTE] Portal alternative
> In the Foundry portal: open your account → **+ New project** → name it → create.

---

## Step 3 — Deploy a chat model (`gpt-4.1-mini`)

> [!IMPORTANT]
> Use `gpt-4.1-mini` (version `2025-04-14`), **not** `gpt-4o-mini`.
> `gpt-4o-mini` was deprecated on 2026-03-31 and the deployment API rejects it with `ServiceModelDeprecated`.

```bash
az cognitiveservices account deployment create \
  --name "$ACCT" \
  --resource-group "$RG" \
  --deployment-name gpt-4-1-mini \
  --model-name gpt-4.1-mini \
  --model-version 2025-04-14 \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 30
```

Key flags:
- `--deployment-name gpt-4-1-mini` — this becomes your `FOUNDRY_MODEL` env value
- `--sku-capacity 30` — 30 K TPM. **Demo 5 (5-agent workflow) needs ≥10 K TPM** to avoid `Too Many Requests`.

Verify:
```bash
az cognitiveservices account deployment show \
  --name "$ACCT" --resource-group "$RG" --deployment-name gpt-4-1-mini \
  --query "{name:name, model:properties.model.name, state:properties.provisioningState, capacity:sku.capacity}" -o table
```

> [!TIP] Discover available models in your region
> ```bash
> az cognitiveservices model list --location "$LOC" \
>   --query "[?model.name=='gpt-4.1-mini'].{version:model.version}" -o table
> ```

> [!NOTE] Portal alternative
> Foundry portal → your project → **Models + endpoints** → **+ Deploy model** → select `gpt-4.1-mini` → Standard, 30 K.

---

## Step 4 — Provision Grounding with Bing Search

Demos 2, 4, and 5 use Bing-grounded web search. This requires a **separate `Microsoft.Bing/accounts` resource** (NOT a Cognitive Services account).

> [!WARNING]
> `Bing.Grounding` is **not in `az cognitiveservices account list-kinds`**. Don't try `az cognitiveservices account create --kind Bing.Grounding` — that won't work. Use raw `az resource create` against `Microsoft.Bing/accounts`.

```bash
az resource create \
  --resource-group "$RG" \
  --name "$BING_RES" \
  --resource-type Microsoft.Bing/accounts \
  --location global \
  --is-full-object \
  --properties '{
    "location": "global",
    "sku": {"name": "G1"},
    "kind": "Bing.Grounding",
    "tags": {"workshop": "agent-framework"}
  }'
```

Capture the resource's full ARM ID — you'll need it for the connection metadata and for cleanup:

```bash
export BING_RESOURCE_ID="$(az resource show -g "$RG" -n "$BING_RES" --resource-type Microsoft.Bing/accounts --query id -o tsv)"
echo "$BING_RESOURCE_ID"
```

Get the API key. The standard `az resource invoke-action --action listKeys` returns `{}` for this resource type — use `az rest` instead:

```bash
export BING_KEY="$(az rest --method POST \
  --url "https://management.azure.com${BING_RESOURCE_ID}/listKeys?api-version=2020-06-10" \
  --query key1 -o tsv)"
echo "Got Bing key (last 4): ...${BING_KEY: -4}"
```

> [!NOTE] Portal alternative
> Azure Portal → **+ Create a resource** → search "Grounding with Bing Search" → SKU G1 → create. Then **Keys and Endpoint** to get the key.

---

## Step 5 — Wire Bing as a Foundry project connection

The Bing resource alone isn't enough — Foundry agents talk to it through a **project-scoped connection**. Create one with `az rest`:

```bash
az rest --method PUT \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ/connections/bing-conn?api-version=2025-04-01-preview" \
  --body @- <<EOF
{
  "properties": {
    "category": "GroundingWithBingSearch",
    "target": "https://api.bing.microsoft.com/",
    "authType": "ApiKey",
    "credentials": {"key": "$BING_KEY"},
    "metadata": {
      "ResourceId": "$BING_RESOURCE_ID",
      "location": "global",
      "type": "bing_grounding"
    }
  }
}
EOF
```

Capture the connection's full resource ID — this is your **`BING_CONNECTION_ID`**:

```bash
export BING_CONNECTION_ID="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ/connections/bing-conn"
echo "$BING_CONNECTION_ID"
```

Verify it's visible to the project:

```bash
az rest --method GET \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ/connections?api-version=2025-04-01-preview" \
  --query "value[].{name:name, category:properties.category, target:properties.target}" -o table
```

> [!IMPORTANT]
> The demos pass `BING_CONNECTION_ID` to a `BingGroundingSearchConfiguration.project_connection_id` field. The field name **`project_connection_id` is not interchangeable with `connection_id`** — using the wrong one is silently accepted but does nothing. The repo's helper functions (`_build_bing_grounding_tool` in `src/demo2_web_search.py`) already handle this correctly.

> [!NOTE] Portal alternative
> Foundry portal → your project → **Settings** → **Connected resources** → **+ New connection** → **Grounding with Bing Search** → pick the Step 4 resource → save.

---

## Step 6 — (Optional) Separate Azure OpenAI for Demo 6

Demo 6 (DevUI) loads the `ai_genius_workflow` entity which uses an **Azure OpenAI account directly** (not via Foundry). This is by design — the entity demonstrates `OpenAIChatCompletionClient` against a vanilla AOAI deployment.

If you don't run Demo 6, skip this step. Otherwise:

```bash
az cognitiveservices account create \
  --name "$AOAI_ACCT" \
  --resource-group "$RG" \
  --kind OpenAI \
  --sku S0 \
  --location "$LOC" \
  --custom-domain "$AOAI_ACCT" \
  --yes \
  --tags workshop=agent-framework

az cognitiveservices account deployment create \
  --name "$AOAI_ACCT" \
  --resource-group "$RG" \
  --deployment-name gpt-4-1-mini \
  --model-name gpt-4.1-mini \
  --model-version 2025-04-14 \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 30
```

> [!NOTE] Portal alternative
> Azure Portal → **+ Create** → "Azure OpenAI" → S0 → create → **Model deployments** → **+ Create new** → `gpt-4.1-mini` Standard.

---

## Step 7 — Capture endpoints + keys

You need 4 values for `.env`:

```bash
# 1) Foundry project endpoint
export FOUNDRY_PROJECT_ENDPOINT="$(az rest --method GET \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ?api-version=2025-04-01-preview" \
  --query "properties.endpoints.\"AI Foundry API\"" -o tsv)"
echo "FOUNDRY_PROJECT_ENDPOINT=$FOUNDRY_PROJECT_ENDPOINT"

# 2) Foundry model deployment name (the same name you used in Step 3)
export FOUNDRY_MODEL="gpt-4-1-mini"

# 3) Bing connection ID (already captured in Step 5)
echo "BING_CONNECTION_ID=$BING_CONNECTION_ID"

# 4) (Optional, Demo 6 only) Azure OpenAI endpoint + key + deployment
export AZURE_OPENAI_ENDPOINT="$(az cognitiveservices account show -n "$AOAI_ACCT" -g "$RG" --query properties.endpoint -o tsv)"
export AZURE_OPENAI_API_KEY="$(az cognitiveservices account keys list -n "$AOAI_ACCT" -g "$RG" --query key1 -o tsv)"
export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="gpt-4-1-mini"
```

---

## Configure your `.env`

In the repo root, copy `.env.example` to `.env` (gitignored), then fill in the values from Step 7:

```bash
cp .env.example .env
chmod 600 .env  # protect from group/world reads
```

Edit `.env`:

```env
# ===== Microsoft Foundry =====
FOUNDRY_PROJECT_ENDPOINT=https://<acct>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=gpt-4-1-mini

# ===== Bing Grounding connection (Demos 2, 4, 5) =====
# IMPORTANT: full ARM resource ID, NOT the connection name
BING_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<acct>/projects/<project>/connections/bing-conn

# ===== Azure OpenAI (Demo 6 only) =====
AZURE_OPENAI_ENDPOINT=https://<aoai-acct>.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4-1-mini
AZURE_OPENAI_API_KEY=<your-key>
```

| `.env` variable | Source |
|-----------------|--------|
| `FOUNDRY_PROJECT_ENDPOINT` | Step 7, command 1 |
| `FOUNDRY_MODEL` | Step 3 — your deployment name |
| `BING_CONNECTION_ID` | Step 5 — the **full ARM ID**, not just the name |
| `AZURE_OPENAI_ENDPOINT` | Step 7, command 4 |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | Step 6 — your AOAI deployment name |
| `AZURE_OPENAI_API_KEY` | Step 7, command 4 |

> [!WARNING]
> `.env` is in `.gitignore` — don't `git add` it. Verify with `git check-ignore .env`.

---

## Smoke test the demos

From the repo root:

```bash
pip install -r requirements.txt   # if not done already

# Demo 1 — single agent (no Bing needed)
python3 -u src/demo1_run_agent.py

# Demo 2 — Bing-grounded web search
python3 -u src/demo2_web_search.py

# Demo 3 — MCP via npx (sequential-thinking)
python3 -u src/demo3_hosted_mcp.py

# Demo 4 — structured output + Bing
python3 -u src/demo4_structured_output.py

# Demo 5 — multi-agent workflow (5 stages, uses Bing + code interpreter)
python3 -u src/demo5_workflow_edges.py

# Demo 6 — DevUI server (needs Azure OpenAI for ai_genius entity)
python3 -u src/demo6_devui.py     # opens http://localhost:8080

# Demo 7 — Foundry Toolboxes / Hosted Agent V2 (fail-soft if not configured)
python3 -u src/demo7_toolbox.py
```

### Expected outcomes

| Demo | What "PASS" looks like |
|------|------------------------|
| 1 | Single venue specialist returns a 1-page event plan |
| 2 | Returns a list of real Seattle venues (Gray Sky Gallery, Studio Forma, etc.) cited from web |
| 3 | Multi-step "Thought 1/10 …" boxes printed via MCP, then a final plan |
| 4 | `VenueOptionsModel` parsed and printed as 4 venues with title/address/services/cost |
| 5 | All 5 agents run in sequence; "Workflow Result:" with per-executor sections |
| 6 | DevUI homepage at `http://localhost:8080` returns HTTP 200; `/v1/entities` lists `Event Planning Workflow` with all 5 agents |
| 7 | Prints `[Toolbox demo] Skipped` and `[Hosted Agent demo] Skipped` (graceful no-op) |

---

## Troubleshooting

These are real issues we hit during the May 6, 2026 validation. Each one cost a smoke retry.

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| `ServiceModelDeprecated: gpt-4o-mini ... has been deprecated since 03/31/2026` | Default in older `.env.example` | Use `gpt-4.1-mini` version `2025-04-14` (Step 3) |
| `Too Many Requests` from Demo 5 | Default 1 K TPM not enough for 5-agent workflow | `--sku-capacity 30` (Step 3) or `az rest PATCH .../deployments/<name>` |
| `TypeError: Object of type WebSearchConfiguration is not JSON serializable` | Tried `client.get_web_search_tool(custom_search_configuration=...)` | The repo's helper uses `BingGroundingTool` from `azure.ai.projects.models` + `.as_dict()` — already fixed in `src/demo2_web_search.py` |
| `TypeError: Object of type CodeInterpreterTool is not JSON serializable` | Same root cause for code interpreter | `client.get_code_interpreter_tool().as_dict()` — already fixed |
| `TypeError: Agent.run() got an unexpected keyword argument 'response_format'` | 1.2.2 API change | Pass `options={"response_format": ...}` — already fixed in `src/demo4_structured_output.py` |
| `AttributeError: 'Workflow' object has no attribute 'run_stream'` | 1.2.2 unified streaming | `workflow.run(prompt, stream=True)` — already fixed in `src/demo5_workflow_edges.py` |
| `az resource invoke-action ... listKeys` returns `{}` | Bing resource doesn't expose listKeys via this CLI | Use `az rest --method POST .../listKeys` (Step 4) |
| `az cognitiveservices account delete --yes` rejected | `--yes` not in some CLI versions | Drop `--yes`; the command is non-interactive by default |
| Bing Grounding silently doesn't work | Wrong connection field name | Use `project_connection_id` on `BingGroundingSearchConfiguration` (the repo helper does this) |
| Demo 5 hits "Too Many Requests" mid-run | Token rate spike | Bump deployment SKU to 30 K TPM mid-run via `az rest PATCH` (no recreate needed) |
| `--tag` and `--location` conflict with default location set | CLI default location collides with tag query | `az configure --defaults location=""` first |

---

## Cleanup / teardown

The cleanup commands assume you've **tagged everything you created** with `workshop=agent-framework` (the recipes above do this). Use the tag to scope deletion:

### One-liner (fastest, but verify first!)

```bash
az resource list --tag workshop=agent-framework --query "[].id" -o tsv | \
  xargs -r -I {} az resource delete --ids {}
```

> [!WARNING]
> The `--tag` query returns ALL resources with that tag across your subscription. If you have other resources tagged `workshop=agent-framework`, they will be deleted too. Verify first:
> ```bash
> az resource list --tag workshop=agent-framework --query "[].{name:name, type:type, rg:resourceGroup}" -o table
> ```

### Per-resource (safer)

```bash
# 1. Delete Foundry project Bing connection
az rest --method DELETE \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ/connections/bing-conn?api-version=2025-04-01-preview"

# 2. Delete Bing resource
az resource delete -g "$RG" -n "$BING_RES" --resource-type Microsoft.Bing/accounts

# 3. Delete model deployment from Foundry account (keeps the account itself)
az cognitiveservices account deployment delete -n "$ACCT" -g "$RG" --deployment-name gpt-4-1-mini

# 4. (Optional) Delete the Foundry project itself
az rest --method DELETE \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCT/projects/$PROJ?api-version=2025-04-01-preview"

# 5. (Optional) Delete the Foundry account
az cognitiveservices account delete -n "$ACCT" -g "$RG"
az cognitiveservices account purge -n "$ACCT" -g "$RG" --location "$LOC"

# 6. Delete the AOAI account (cascades the deployment)
az cognitiveservices account delete -n "$AOAI_ACCT" -g "$RG"
az cognitiveservices account purge -n "$AOAI_ACCT" -g "$RG" --location "$LOC"

# 7. (Nuclear option) Delete the entire resource group
az group delete -n "$RG" --yes --no-wait
```

> [!IMPORTANT]
> Cognitive Services accounts use **soft-delete**. After `account delete`, you must also **purge** them or you can't reuse the same name within 48 hours. The purge step is shown above.

### Verify cleanup

```bash
az resource list --tag workshop=agent-framework --query "[].name" -o tsv  # → empty
az resource list -g "$RG" -o table                                        # → empty (or just RG itself)
az cognitiveservices account list-deleted --query "[?name=='$ACCT' || name=='$AOAI_ACCT']"  # → []
```

---

## Cost reference

Actuals from the May 6, 2026 validation run that ran all 7 demos end-to-end:

| Demo | Tokens consumed | Bing queries | Cost |
|------|-----------------|-------------:|-----:|
| Demo 1 | ~3 K total | 0 | ~$0.001 |
| Demo 2 | ~5 K total | 1 | ~$0.026 |
| Demo 3 | ~12 K total (10 thinking steps) | 0 | ~$0.003 |
| Demo 4 | ~5 K total | 1 | ~$0.026 |
| Demo 5 | ~30 K total (5 agents) | 4 | ~$0.110 |
| Demo 6 | 0 (server boot only) | 0 | ~$0.000 |
| Demo 7 | 0 (fail-soft) | 0 | ~$0.000 |
| **Total** | **~55 K** | **6** | **~$0.17** |

Plus an idle cost of $0 (no per-hour fees on any resource here). Plus a small allowance for resource creation overhead (~$0.05) and a buffer for retries (~$0.30) → **typical full-validation budget: $0.50–1.00**.

> [!TIP]
> Set a **subscription budget alert** at $5 to catch any runaway costs:
> ```bash
> az consumption budget create \
>   --budget-name workshop-cap \
>   --amount 5 \
>   --time-grain Monthly \
>   --start-date "$(date -u +%Y-%m-01)" \
>   --end-date "$(date -u -d '+3 months' +%Y-%m-01)" \
>   --category Cost
> ```

---

## What this guide does NOT cover

| Out of scope | Why |
|--------------|-----|
| **Hosted Agent V2** provisioning (`Microsoft.App/agents`) | Public preview as of May 5, 2026; not yet validated end-to-end. Demo 7 is fail-soft for now. |
| **Foundry Toolboxes** provisioning | Same — public preview, not yet GA. |
| **Foundry Local** (`agent-framework-foundry-local`) | Local model runtime, separate setup story |
| **Bicep / Terraform / `azd up` templates** | Future work; this guide is CLI-step focused for clarity |
| **Private VNet / private endpoints** | Out of scope; would require a separate networking guide |
| **Customer-managed keys (CMK)** | Out of scope; uses platform-managed keys |
| **Multi-region active-active** | Single-region single-project here |

---

## Validation snapshot

This guide was last validated on **May 6, 2026** by following these exact steps end-to-end against `MCAPS-Hybrid-REQ-118084-2025-syanagihara` in `eastus2`. All 7 demos in this repository (`src/demo1_run_agent.py` through `src/demo7_toolbox.py`) ran to completion. Total cost: **$0.50**. Total wall-clock time from "az login" to "Demo 7 PASS": **~30 minutes** (most of it was waiting for resource provisioning).

If you find a step that doesn't work as documented, please open an issue on the repo with:
- The command you ran
- The full error message
- Your `az --version` output
- Your subscription tenant + region

Re-validation should happen after each major Agent Framework upgrade per [`AGENTS.md`](../AGENTS.md).
