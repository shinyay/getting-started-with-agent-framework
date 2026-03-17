---
layout: step
title: "Web Search Tool"
step_number: 2
permalink: /steps/2/
---

# Exercise 2 — Add Hosted Web Search Tool

| | |
|---|---|
| **Phase** | 1 — Foundations |
| **Difficulty** | ⭐ |
| **Estimated time** | 20–30 min |
| **Starter file** | `starter.py` (3 TODOs) |

---

## Learning Objectives

By completing this exercise you will be able to:

- Explain what **hosted tools** are and how they differ from local tools
- Instantiate `HostedWebSearchTool` with the correct configuration
- Configure a **Bing grounding connection** for your Foundry project
- Pass tools to an agent via `as_agent(tools=[...])`

## Prerequisites

| Requirement | Details |
|---|---|
| Exercise 1 completed | You can create and run a basic agent |
| `BING_CONNECTION_ID` env var | Set in `.env` (see [Background](#background) below) |
| Azure AI Foundry project | Same project used in Exercise 1 |

## Background

### Hosted Tools

The Agent Framework supports **hosted tools** — tools that execute on the Azure AI Foundry service side, not in your local process. When you attach a hosted tool to an agent:

1. Your code sends the tool *definition* to Foundry when creating the agent.
2. The model decides when to invoke the tool (you don't call it yourself).
3. Foundry runs the tool server-side and feeds the result back to the model.

`HostedWebSearchTool` is a hosted tool backed by **Bing grounding**. It lets the agent search the web for current information without you writing any HTTP/search logic.

### Bing Grounding Connection

To use Bing grounding you need a **Foundry project connection**, not a raw Bing API key.

How to create one:

1. Open your Azure AI Foundry project in the portal.
2. Go to **Management → Connected resources** (or **Settings → Connections**).
3. Click **+ New connection → Grounding with Bing Search**.
4. Select or create a Bing Search resource, then save.
5. Copy the **project connection ID** — it looks like:
   ```
   /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project>/connections/<name>
   ```
6. Set it as `BING_CONNECTION_ID` in your `.env` file.

### How the Agent Decides to Search

The model uses its instructions and the conversation context to decide whether to invoke the web search tool. You can influence this by:

- Wording your instructions to mention web search capabilities
- Asking questions about current/real-time information

## Your Task

Open `starter.py`. The helper code (`.env` loading, DNS check, Bing config) is already provided. You need to fill in **3 TODOs** inside `async def main()`:

### Step 1 — Create the `HostedWebSearchTool` (TODO 1)

Create a `HostedWebSearchTool` instance with `additional_properties` that includes:
- A `user_location` dict (e.g., `{"city": "Seattle", "country": "US"}`)
- The Bing connection properties from `bing_props`

### Step 2 — Create the Agent with the Tool (TODO 2)

Use `AzureAIAgentClient(credential=cred).as_agent(...)` to create an agent with:
- A `name` (e.g., `"web_search"`)
- `instructions` that tell the agent it can search the web
- `tools=[...]` containing your `HostedWebSearchTool` instance

Remember to use `async with` so the agent is properly cleaned up.

### Step 3 — Run the Agent and Print the Result (TODO 3)

Call `agent.run()` with a search query and print `result.text`. Wrap the call in a `try/except ServiceResponseException` to handle model resolution errors gracefully.

## Hints

Work through the hints one at a time — try each step on your own first!

<details>
<summary>💡 Hint 1 — HostedWebSearchTool takes additional_properties</summary>

```python
HostedWebSearchTool(
    additional_properties={
        "user_location": {"city": "...", "country": "..."},
        # ... bing connection config goes here too
    }
)
```

The `additional_properties` dict is where you pass both the user location and the Bing connection settings.

</details>

<details>
<summary>💡 Hint 2 — Use _get_bing_tool_properties() and merge dicts</summary>

The starter code already calls `bing_props = _get_bing_tool_properties()`. This returns a dict like `{"connection_id": "..."}`.

Merge it with user_location using `**` unpacking:

```python
additional_properties={
    "user_location": {"city": "Seattle", "country": "US"},
    **bing_props,
}
```

</details>

<details>
<summary>💡 Hint 3 — Near-complete solution</summary>

```python
# TODO(1)
web_search_tool = HostedWebSearchTool(
    additional_properties={
        "user_location": {"city": "Seattle", "country": "US"},
        **bing_props,
    }
)

# TODO(2)
async with AzureAIAgentClient(credential=cred).as_agent(
    name="web_search",
    instructions=(
        "You are a web search expert who can find current information on the web "
        "to help plan events and answer questions."
    ),
    tools=[web_search_tool],
) as agent:
    # TODO(3)
    try:
        result = await agent.run(
            "What venue could hold 50 people on December 6th, 2026 in Seattle"
        )
    except ServiceResponseException as ex:
        msg = str(ex)
        if "Failed to resolve model info" in msg:
            raise RuntimeError(
                "Could not resolve model deployment. "
                "Check AZURE_AI_MODEL_DEPLOYMENT_NAME in the Foundry portal."
            ) from ex
        raise

    print(result.text)
```

</details>

## Validate Your Work

### 1. Run the structure check

```bash
bash workshop/exercises/ex2_web_search/check.sh
```

All checks should show ✅.

### 2. Run against Azure

```bash
python workshop/exercises/ex2_web_search/starter.py
```

You should see a response with web search results about venues in Seattle (or your chosen location). The response will include real, current information from the web.

## Bonus Challenges

- **Change the user location**: Try `{"city": "Tokyo", "country": "JP"}` and ask a location-specific question. Does the result change?
- **Control when search triggers**: Modify the agent instructions to say "Only use web search when the user explicitly asks for current information." Then compare responses with and without a search-triggering prompt.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `RuntimeError: Hosted web search requires a Bing connection` | `BING_CONNECTION_ID` not set or empty | Set it in `.env` — get the value from the Foundry portal |
| `BING_CONNECTION_ID` value looks wrong | Wrong format — needs full ARM resource path | Use the full connection ID starting with `/subscriptions/...` |
| `Failed to resolve model info` | Model deployment name mismatch | Open Foundry portal → Models + endpoints → use the exact deployment name |
| `Cannot resolve ... host via DNS` | Private networking / DNS issue | Run from a network that can resolve the Foundry endpoint, or use a public project |

## Solution Reference

The complete working solution is at [`src/demo2_web_search.py`](../../../src/demo2_web_search.py).

---

> **Reference**: The `HostedWebSearchTool` API is part of `agent-framework` (pinned at `1.0.0b260123` in this repository). If Microsoft Learn docs show different behavior, the pinned version and `src/demo2_web_search.py` take precedence.
