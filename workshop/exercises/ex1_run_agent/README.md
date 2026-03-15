# Exercise 1 — Create and Run Your First Agent

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 1 — Foundations | ⭐ Beginner | 15–20 min |

## Learning Objectives

By the end of this exercise you will be able to:

1. Create an `AzureAIAgentClient` backed by Entra ID credentials
2. Use `.as_agent()` to define an agent with a **name** and **instructions**
3. Call `agent.run()` with a user prompt and read the response via `result.text`

---

## Prerequisites

| Requirement | How to verify |
|-------------|--------------|
| Environment setup complete | `python3 -c "import agent_framework; print(agent_framework.__version__)"` |
| Azure CLI logged in | `az account show` (should return your subscription) |
| `.env` configured | Ensure `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME` are set in the repo-root `.env` |

---

## Background

### The 3-Layer Architecture

```
┌──────────────────────────────────┐
│  Azure AI Foundry Project        │  ← Cloud resource (models, connections, storage)
├──────────────────────────────────┤
│  Environment Variables (.env)    │  ← AZURE_AI_PROJECT_ENDPOINT,
│                                  │    AZURE_AI_MODEL_DEPLOYMENT_NAME
├──────────────────────────────────┤
│  Your Python Code                │  ← AzureAIAgentClient → agent → run()
└──────────────────────────────────┘
```

### Key Concepts

- **`AzureAIAgentClient`** — The client that connects to your Azure AI Foundry project. It reads `AZURE_AI_PROJECT_ENDPOINT` and `AZURE_AI_MODEL_DEPLOYMENT_NAME` from environment variables automatically.
- **`.as_agent(name=..., instructions=...)`** — Creates a hosted agent with a persona. The `name` identifies the agent; `instructions` define its system-level behaviour.
- **`agent.run(prompt)`** — Sends a user message to the agent and returns a result object. Access the agent's text reply via `result.text`.

> **Note:** Both the credential and the agent client are **async** resources. Always use `async with` to ensure they are properly closed.

---

## Your Task

Open `starter.py` in this directory. You will see three `TODO` markers inside `async def main()`. Fill them in:

### Step 1 — Create an `AzureCliCredential` (TODO 1)

Create an async context manager for `AzureCliCredential`:

```python
async with AzureCliCredential() as cred:
```

This authenticates against Azure using the CLI token from `az login`.

### Step 2 — Create the Agent (TODO 2)

Inside the credential block, create an agent using `AzureAIAgentClient`:

```python
async with AzureAIAgentClient(credential=cred).as_agent(
    name="venue_specialist",
    instructions="You are the Venue Specialist, an expert in venue research and recommendation.",
) as agent:
```

- `credential=cred` passes the Entra ID credential to the client.
- `.as_agent()` creates a hosted agent on Foundry with the given name and instructions.
- The `async with` block ensures the agent is cleaned up when done.

### Step 3 — Run the Agent (TODO 3)

Call `agent.run()` with a prompt and print the result:

```python
result = await agent.run(
    "Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
)
print("Result:\n")
print(result.text)
```

---

## Hints

Work through the hints progressively — try on your own first!

<details>
<summary>💡 Hint 1 — High-level approach</summary>

Both `AzureCliCredential()` and the agent must be used as `async with` context managers. Nest them inside `main()`:

```python
async with <credential> as cred:
    async with <agent_client>.as_agent(...) as agent:
        result = await agent.run(...)
```

</details>

<details>
<summary>💡 Hint 2 — Client and agent creation</summary>

`AzureAIAgentClient` takes a `credential=` parameter. You then chain `.as_agent()` on it to create the agent:

```python
AzureAIAgentClient(credential=cred).as_agent(
    name="venue_specialist",
    instructions="You are the Venue Specialist, ...",
)
```

No need to pass the endpoint or model name — those are read from environment variables automatically.

</details>

<details>
<summary>💡 Hint 3 — Near-complete solution</summary>

```python
async with AzureCliCredential() as cred:
    async with AzureAIAgentClient(credential=cred).as_agent(
        name="venue_specialist",
        instructions="You are the Venue Specialist, an expert in venue research and recommendation.",
    ) as agent:
        result = await agent.run(
            "Plan a corporate holiday party for 50 people on December 6th, 2026 in Seattle"
        )
        print("Result:\n")
        print(result.text)
```

</details>

---

## Validate Your Work

### 1. Run the check script (offline — no Azure needed)

```bash
bash workshop/exercises/ex1_run_agent/check.sh
```

This verifies syntax, required code patterns, and that all TODOs are resolved.

### 2. Run against Azure

```bash
python3 -u workshop/exercises/ex1_run_agent/starter.py
```

**Expected behaviour:**

- The script connects to your Foundry project.
- The agent generates a party-planning response (venue suggestions, logistics, etc.).
- You see `Result:` followed by the agent's text output.
- If OpenTelemetry is available, `[AGENT]` span lines appear showing the agent invocation.

---

## Bonus Challenges

1. **Change the agent name and instructions** — Try `name="travel_advisor"` with travel-themed instructions. How does the response change?
2. **Try different prompts** — Ask for a different scenario (e.g., "Plan a 3-day team offsite in Tokyo for 20 engineers").
3. **Observe OpenTelemetry spans** — Look at the `[AGENT]` and `[TOOL]` lines in the output. What information do they capture?

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `DefaultAzureCredential` / auth error | Not logged in to Azure CLI | Run `az login` and retry |
| `Cannot resolve ... host via DNS` | Foundry project uses private networking | Use a public endpoint or run from a network that can resolve the private DNS |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` missing | `.env` not configured | Copy `.env.example` to `.env` and set the deployment name to match your Foundry project |
| `RuntimeError: Required environment variable ...` | Missing or empty env var | Check `.env` at the repo root — ensure values are not empty strings |
| `ModuleNotFoundError: agent_framework` | Dependencies not installed | Run `pip install -r requirements.txt` |

---

## Solution Reference

See the complete working solution at: **`src/demo1_run_agent.py`**
