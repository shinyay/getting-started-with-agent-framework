# Exercise 4 — Structured Output with Pydantic

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 2 — Integration | ⭐⭐ Intermediate | 20–25 min |

## Learning Objectives

By the end of this exercise you will be able to:

1. Define **Pydantic `BaseModel` schemas** to describe the shape of agent output
2. Use the **`response_format`** parameter on `agent.run()` to request structured data
3. Access the parsed result via **`response.value`** and handle the fallback through **`response.text`**

---

## Prerequisites

| Requirement | How to verify |
|-------------|--------------|
| Exercise 3 completed | You have run Ex 3 successfully |
| `pydantic` installed | `python3 -c "import pydantic; print(pydantic.__version__)"` |
| Bing connection configured | `BING_CONNECTION_ID` (or equivalent) is set in repo-root `.env` |
| Azure CLI logged in | `az account show` (should return your subscription) |

---

## Background

### Why Structured Output?

When an LLM is used as a **component in an automation pipeline** — not just a chatbot — you need its output in a predictable, typed format. Free-form text is hard to route, store, or display in a UI.

**Structured output** solves this: you provide a JSON schema (derived from a Pydantic model), and the agent returns data that conforms to that schema.

### How It Works in Agent Framework

```
┌─────────────────────────────────────────────────────────────┐
│  1. Define a Pydantic BaseModel                             │
│     class VenueInfoModel(BaseModel):                        │
│         title: str | None = None                            │
│         estimated_cost_per_person: float = 0.0              │
├─────────────────────────────────────────────────────────────┤
│  2. Pass the model as response_format to agent.run()        │
│     response = await agent.run(                             │
│         "Find venues...",                                   │
│         response_format=VenueOptionsModel,                  │
│     )                                                       │
├─────────────────────────────────────────────────────────────┤
│  3. Access the result                                       │
│     response.value  → parsed Pydantic instance (or None)    │
│     response.text   → raw text (fallback)                   │
└─────────────────────────────────────────────────────────────┘
```

- **`response.value`** — The SDK attempts to parse the agent's output into your Pydantic model automatically. If successful, this is a fully typed Python object.
- **`response.text`** — The raw text reply. Some backends/SDK versions return the JSON string here instead of populating `.value`. Always plan a **fallback**: if `.value` is `None`, try `YourModel.model_validate_json(response.text)`.

> **Tip:** The fallback parsing logic is provided for you in the starter. It's important in production, but not the learning focus of this exercise.

---

## Your Task

Open `starter.py` in this directory. You will see five `TODO` markers. Fill them in:

### Step 1 — Define `VenueInfoModel` (TODO 1)

Create a Pydantic `BaseModel` that describes a single venue:

| Field | Type | Default |
|-------|------|---------|
| `title` | `str \| None` | `None` |
| `description` | `str \| None` | `None` |
| `services` | `str \| None` | `None` |
| `address` | `str \| None` | `None` |
| `estimated_cost_per_person` | `float` | `0.0` |

```python
class VenueInfoModel(BaseModel):
    """Information about a venue."""
    title: str | None = None
    # ... add the remaining fields
```

### Step 2 — Define `VenueOptionsModel` (TODO 2)

Create a second model that wraps a **list** of `VenueInfoModel`:

```python
class VenueOptionsModel(BaseModel):
    """Options for a venue."""
    options: list[VenueInfoModel]
```

### Step 3 — Create the Agent with Web Search (TODO 3)

Reuse the Bing configuration pattern from Exercise 2. Create an agent with `HostedWebSearchTool`:

```python
async with AzureAIAgentClient(credential=cred) as client:
    async with client.as_agent(
        name="venue_specialist",
        instructions="...",
        tools=[HostedWebSearchTool(additional_properties={...})],
    ) as agent:
```

- Pass `bing_props` (already computed for you) in `additional_properties`.
- Include `"user_location"` as well if you'd like location-aware results.

### Step 4 — Call `agent.run()` with `response_format` (TODO 4)

This is the key new concept — pass your Pydantic model class to `response_format`:

```python
response = await agent.run(
    "Find venue options for a corporate holiday party for 50 people on December 6th, 2026 in Seattle",
    response_format=VenueOptionsModel,
)
```

> **Important:** `response_format` is a keyword argument to `agent.run()`, **not** to `.as_agent()`.

### Step 5 — Extract and Display Structured Data (TODO 5)

Access the parsed result and print each venue's fields:

```python
venue_options = response.value
if venue_options:
    for option in venue_options.options:
        print(f"Title: {option.title}")
        # ... print the remaining fields
```

---

## Hints

Work through the hints progressively — try on your own first!

<details>
<summary>💡 Hint 1 — Field types and defaults</summary>

Use `str | None = None` for optional string fields and `float = 0.0` for numeric defaults:

```python
class VenueInfoModel(BaseModel):
    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0
```

</details>

<details>
<summary>💡 Hint 2 — Where does response_format go?</summary>

`response_format` is a keyword argument to `agent.run()`, **not** to `as_agent()`:

```python
# ✅ Correct
response = await agent.run("...", response_format=VenueOptionsModel)

# ❌ Wrong — as_agent() does not accept response_format
client.as_agent(name=..., response_format=VenueOptionsModel)
```

</details>

<details>
<summary>💡 Hint 3 — Near-complete solution</summary>

```python
class VenueInfoModel(BaseModel):
    """Information about a venue."""
    title: str | None = None
    description: str | None = None
    services: str | None = None
    address: str | None = None
    estimated_cost_per_person: float = 0.0

class VenueOptionsModel(BaseModel):
    """Options for a venue."""
    options: list[VenueInfoModel]

# Inside main():
async with AzureAIAgentClient(credential=cred) as client:
    async with client.as_agent(
        name="venue_specialist",
        instructions=(
            "You are the Venue Specialist, an expert in venue research and recommendation. "
            "Use web search to find venue options and return only structured data that matches the provided schema."
        ),
        tools=[
            HostedWebSearchTool(
                additional_properties={
                    "user_location": {"city": "Seattle", "country": "US"},
                    **bing_props,
                }
            )
        ],
    ) as agent:
        response = await agent.run(
            "Find venue options for a corporate holiday party for 50 people on December 6th, 2026 in Seattle",
            response_format=VenueOptionsModel,
        )

        venue_options = response.value
        if venue_options:
            for option in venue_options.options:
                print(f"Title: {option.title}")
                print(f"Address: {option.address}")
                print(f"Description: {option.description}")
                print(f"Services: {option.services}")
                print(f"Cost per person: {option.estimated_cost_per_person}")
                print()
```

</details>

---

## Validate Your Work

### 1. Run the check script (offline — no Azure needed)

```bash
bash workshop/exercises/ex4_structured_output/check.sh
```

This verifies syntax, required code patterns, and that all TODOs are resolved.

### 2. Run against Azure

```bash
python3 -u workshop/exercises/ex4_structured_output/starter.py
```

**Expected behaviour:**

- The script connects to your Foundry project and creates a `venue_specialist` agent.
- The agent searches the web (via Bing) for venue options.
- The response is parsed into `VenueOptionsModel` — a list of `VenueInfoModel` instances.
- You see structured output like:

```
Title: The Ballroom at ...
Address: 123 Main St, Seattle, WA
Description: An elegant event space ...
Services: Full catering, AV equipment ...
Cost per person: 85.0
```

- If `response.value` is `None`, the fallback logic parses `response.text` as JSON and still produces structured output.

---

## Bonus Challenges

1. **Design your own model** — Create a Pydantic `BaseModel` for a different domain (e.g., `RecipeModel` with ingredients and steps, or `FlightOptionModel` with airline, price, and duration). Use it as `response_format`.
2. **Add field validators** — Use Pydantic's `@field_validator` to enforce constraints (e.g., `estimated_cost_per_person` must be ≥ 0).
3. **Nested models** — Try adding a nested `AddressModel` inside `VenueInfoModel` with structured street/city/state fields.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `response.value` is `None` | Backend returned JSON in `.text` instead | The provided fallback logic handles this — check the console for "(parsed from response.text)" |
| `ValidationError` from Pydantic | Schema fields don't match agent output | Ensure your field names and types match the model definitions exactly |
| `RuntimeError: Hosted web search requires a Bing connection` | `BING_CONNECTION_ID` not set | Set it in repo-root `.env` — see Exercise 2 for details |
| `Failed to resolve model info` | Deployment name mismatch | Check `AZURE_AI_MODEL_DEPLOYMENT_NAME` in `.env` matches your Foundry project |
| `Cannot resolve ... host via DNS` | Private networking | Use a public endpoint or run from the correct network |
| `ModuleNotFoundError: pydantic` | pydantic not installed | Run `pip install -r requirements.txt` |

---

## Solution Reference

See the complete working solution at: **`src/demo4_structured_output.py`**
