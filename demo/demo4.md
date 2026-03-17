---
layout: cheatsheet
title: "Exercise 4 — Walkthrough"
parent_step: 4
permalink: /cheatsheet/4/
---

# Demo 4 — Structured Output (Getting typed output with response_format)

```text
Reference:
- https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
```

## Objectives
- Define a Pydantic model and run with `response_format=<Model>` specified
- Handle the output safely as `response.value` (= a Pydantic instance)
- Continue the story from Demo 2 (venue search) and **structure the information gathered via Web Search**

---

## Prerequisites
- Demo 2 is complete (Azure AI Foundry Agents env vars are configured)
- `pydantic` is installed (already included in the Dev Container)
- `az login` completed

Additional required env vars:
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

This demo uses Web Search, so a Bing connection is also required (same as Demo 2):
- `BING_CONNECTION_ID` (or `BING_PROJECT_CONNECTION_ID`)
    - Or `BING_CUSTOM_CONNECTION_ID` + `BING_CUSTOM_INSTANCE_NAME`

(Recommended)
- Before running Demo 4, verify the following:
    - `az login` completed (when using Entra ID by default)
    - The `.env` file (at the repository root) contains the required values

---

## Steps

### Step 1. Define the structure (schema) with Pydantic
This repository includes `src/demo4_structured_output.py`.
(You can edit and extend it as needed)

Below is a **minimal example to illustrate the concept**.
For production-grade hardening (explicit `.env` loading, empty-string injection protection, DNS checks, fallback when `response.value` is empty, etc.), refer to the included `src/demo4_structured_output.py`.

```python
from pydantic import BaseModel

class VenueInfoModel(BaseModel):
    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0

class VenueOptionsModel(BaseModel):
    options: list[VenueInfoModel]

# In the actual demo, we use Azure AI Foundry Agents + HostedWebSearchTool
# to ask "find venues" and receive the results via response_format=VenueOptionsModel.
```

Key implementation details (in the included script):
- Explicitly loads the repository root `.env` and **only fills in unset/empty environment variables**
    - This mitigates the empty-string injection issue in Dev Container / Codespaces
- Includes a fallback that restores the Pydantic model even when `response.value` is `None`, as long as `response.text` contains valid JSON
    - This handles cases where the value is not populated in non-streaming mode due to backend/version differences

Note:
- Official/sample code may show examples using `client.create_agent(...)`, but the SDK pinned in this repository uses `as_agent(...)` as the current API, so we follow that convention

(Additional note)
- The included script runs **both non-streaming and streaming** modes, allowing you to verify that `PersonInfo` can be extracted in either case.

### Step 2. Run
```bash
python3 -u src/demo4_structured_output.py
```

### Step 3. Expected output
Multiple venue candidates are output with structured fields (title/address/description/...).

- If `response.value` is populated, it is displayed directly as a Pydantic instance
- If `response.value` is empty but `response.text` contains JSON, it is restored and displayed (fallback)

---

## Technical Explanation (Key concepts)

### 1) `response_format` makes the "output shape" a contract
- It is not just a JSON string
- It **instructs the model to produce output conforming to the specified schema (Pydantic model)**

### 2) `response.value` is the "type-safe result"
- On success, `response.value` contains a **Pydantic instance**
- On failure, it can be `None`, so always check with an if statement

### 3) Notes on streaming
This demo first demonstrates structured output in **non-streaming** mode.
Combining it with streaming is an advanced topic best explored alongside the observations in Demo 5/6.

---

## Common Pitfalls

### `response.value` is `None` in non-streaming mode
The conditions that trigger this depend on the environment (backend/version differences), but the following pattern can occur:

- `response.text` returns JSON, but it is not populated into `response.value` (Pydantic)

Resolution:
- **The included `src/demo4_structured_output.py` already has fallback handling** (`PersonInfo.model_validate_json(...)` restores from `response.text` if it contains JSON)
- In your own code, it is also safe to log `response.text` when `response.value is None` and parse it as JSON if valid

### Structured output does not work
- Not all agent types/backends support structured output
- First, run the Demo 4 code **as-is**, then extend it after confirming it works

### DNS resolution fails before starting
If the host in `AZURE_AI_PROJECT_ENDPOINT` cannot be resolved from the execution environment, execution stops at startup.

- Error example: `Cannot resolve AZURE_AI_PROJECT_ENDPOINT host via DNS`
- Resolution: Review your Private networking / DNS configuration, or run from a network where DNS resolution is possible

Note:
- DNS resolution may succeed on the host environment but fail inside the Dev Container. In that case, check the container's DNS settings (Corporate DNS / Private Link / Dev Container network settings).
- A workaround using `/etc/hosts` with a fixed IP is possible, but it breaks when the IP changes and is not a permanent solution (recommended only as a "last resort" for local testing).

---

## Next Demo
In Demo 5, we split the processing across multiple agents and build a pipeline with guaranteed ordering using **Workflow + Edge**.
→ Open `demo5.md` to continue.
