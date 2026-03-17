---
layout: step
title: "Capstone Project"
step_number: 7
permalink: /steps/7/
---

# Exercise 7 — Capstone Challenge: Build Your Own Agent System

| Phase | Difficulty | Time Estimate |
|-------|-----------|---------------|
| 4 — Capstone | ⭐⭐⭐ Advanced | 45 min (or continue after the workshop) |

## Overview

You've learned the core concepts — agents, tools, structured output, multi-agent workflows, and DevUI.
Now it's time to **build something on your own**.

Choose one of the three challenges below and create a working solution from scratch.
There is no starter code; use what you've learned in Exercises 1–6 as your foundation.

---

## Challenge Options

### Option A: Custom Function Tool + Agent

Build a Python function that an agent can call as a tool.

**Example ideas**:
- Weather lookup (mock data)
- Database query helper (SQLite)
- File analyzer (word count, structure, etc.)
- Calculator with history

**Requirements**:
1. Define at least one Python function with **type hints** and a **docstring**
2. Register it as a tool for an agent
3. Create an agent that uses the tool based on user input
4. Handle errors gracefully (invalid input, missing data, etc.)

**Evaluation criteria**:
- Tool is callable by the agent
- Agent invokes the tool correctly based on the conversation
- Output is meaningful and well-formatted

---

### Option B: New Domain Multi-Agent Workflow

Design a multi-agent workflow for a **completely different domain** (not event planning).

**Example ideas**:
- Code review pipeline (lint → review → summary)
- Research paper summarizer (search → extract → synthesize)
- Travel itinerary planner (destination → activities → budget)
- Product launch checklist (market research → copy → timeline)

**Requirements**:
1. At least **3 specialist agents** with distinct roles
2. Use `WorkflowBuilder` with edges connecting them
3. Include at least one tool (hosted tool or MCP)
4. Consume streaming events from the workflow execution

**Evaluation criteria**:
- Workflow executes end-to-end without errors
- Each agent produces relevant, domain-specific output
- Events are tracked and displayed during execution

---

### Option C: Extend the Event Planning System

Add a new capability to the existing event planning workflow from Exercise 5/6.

**Example ideas**:
- Add a **Transportation** agent that plans logistics between venues
- Add **structured output** (Pydantic model) to the booking agent
- Create a **DevUI entity** that loads the extended workflow
- Add **conditional routing** (e.g., skip catering for virtual events)

**Requirements**:
1. At least one new agent or a significant enhancement to an existing one
2. Integration with the existing workflow pattern (see `src/demo5_workflow_edges.py`)
3. A DevUI entity that can be loaded (see `entities/event_planning_workflow/`)

**Evaluation criteria**:
- Extended workflow runs without breaking existing agents
- New capability produces useful output
- Entity loads correctly in DevUI (if applicable)

---

## General Requirements (All Options)

Regardless of which challenge you choose, your solution must:

- [ ] Follow the repository's established patterns:
  - Fill-only `.env` loading with `dotenv_values` (don't override existing vars)
  - `_require_env()` for mandatory environment variables
  - `async with` for credentials and clients
- [ ] Handle errors with **actionable messages** (tell the user what to check/fix)
- [ ] Pass syntax checking: `python3 -m compileall -q .`
- [ ] Include a brief comment at the top of your main file explaining what the system does

## Tips

1. **Start by sketching your design** on paper or in a comment block — list agents, tools, and data flow before writing code
2. **Reuse patterns from Exercises 1–6** — copy boilerplate (`.env` loading, credential setup, `_require_env`) from the starter files
3. **Test incrementally** — get one agent working before adding more
4. **Refer to existing solutions** — `src/demo1_run_agent.py` through `src/demo6_devui.py` and `entities/` are your best reference

## Boilerplate Skeleton

Every solution should start with something like this:

```python
"""
Capstone: <brief description of your system>
"""

import asyncio
import os
from pathlib import Path

from dotenv import dotenv_values

# ── .env loading (fill-only) ────────────────────────────────────
_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"
_dotenv = dotenv_values(_DOTENV_PATH)
for _k, _v in _dotenv.items():
    if _v is None:
        continue
    _existing = os.getenv(_k)
    if _existing is None or not _existing.strip():
        os.environ[_k] = _v


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}. "
            "Set it via .env / export / Codespaces secrets and try again."
        )
    return value


async def main() -> None:
    # Your solution here
    ...


if __name__ == "__main__":
    asyncio.run(main())
```

## Sharing

If time permits, **present your solution to the group!** Walk through:
- What challenge you chose and why
- Your design (agents, tools, flow)
- A live run (or key output)
- What you'd improve with more time

## Solution Reference

There is no single correct solution for this exercise — **your creativity is the solution**.

For patterns and inspiration, review:
- `src/demo1_run_agent.py` – `src/demo6_devui.py` (working reference solutions)
- `entities/event_planning_workflow/` (DevUI entity example)
- `entities/ai_genius_workflow/` (alternative workflow example)
