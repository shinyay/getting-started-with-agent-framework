# AGENTS.md

This file defines the working conventions (safety, accuracy, and reproducibility) for working with this repository using **autonomous agents** such as GitHub Copilot Agent mode or coding agents.

## Goals for This Repository
- Implement and validate AI Agents and Workflows **safely and reproducibly** using Python with Microsoft Agent Framework **1.2.2** (+ Microsoft Foundry Agents).
- Important: **Do not guess APIs**. Always base implementations on "the pinned versions in this repository" and primary sources (as needed). Note that 1.0 GA → 1.2.2 introduced many breaking changes from the previous January 2026 RC1-era beta this repo used to ship.

---

## What to Check First (Order Matters)
1. `requirements.txt` / `requirements*.txt`
   - Check the **pinned versions** of agent-framework* (this repo operates on the assumption of pinned versions).
2. `README.md` and `demo/*.md`
   - Review execution steps, environment variables, and expected failures (DNS/permissions/connectivity).
3. `src/demo*.py` and `entities/**`
   - **Prioritize the working examples in this repo** (there may be discrepancies with the docs).

---

## Runtime Environment Assumptions
- OS/Environment: Assumes Dev Container / Codespaces (Linux).
- Python: Assumes 3.11+ (the actual version follows the dev container configuration).
- Authentication: Uses **Entra ID + Azure CLI credential** by default (assumes `az login`).

---

## Default Agent Framework Implementation Patterns (Rules for This Repo)
- **Pinned to `agent-framework-foundry==1.2.2`** (April 29, 2026 stable). Do NOT use the meta `agent-framework` package — installing it overwrites `agent_framework/__init__.py` from `agent-framework-core` and breaks imports.
- For agent creation, prefer the following pattern by default:
  - `FoundryChatClient(project_endpoint=..., model=..., credential=...).as_agent(...)`
- Treat clients/credentials as **async resources** and always guarantee cleanup with `async with`:
  - `azure.identity.aio.AzureCliCredential`
  - `agent_framework.foundry.FoundryChatClient`
- For hosted tools, use the `client.get_*_tool(...)` factory methods (Bing web search, code interpreter, file search, image generation). Do NOT import `HostedWebSearchTool` / `HostedCodeInterpreterTool` — those classes were removed in 1.0 GA.
- For multi-agent workflows, **materialize agent instances first** and pass them to `WorkflowBuilder(start_executor=..., output_executors=[...])`. The 1.2.2 builder requires both kwargs at construction; `register_agent()` and `set_start_executor()` no longer exist.
- For exception handling, use the new hierarchy under `AgentFrameworkException` (e.g., `ChatClientInvalidResponseException`, `AgentInvalidResponseException`). `ServiceResponseException` was removed.
- For UIs/CLIs that require incremental display, prefer `run_stream()`.
  - All workflow events are unified into a single `WorkflowEvent` class with a `type` discriminator (`"data"`, `"executor_completed"`, `"output"`, `"failed"`, etc.). Discriminate with `event.type == "..."` (NOT `isinstance(event, ...)`).

---

## Environment Variables / .env Handling (Required)
- Never expose Secrets/Keys in code, logs, or documentation.
- In Dev Container / Codespaces, environment variables may be **injected as empty strings**, so scripts should follow these defaults:
  - **Explicitly load** the `.env` file from the repository root
  - **Only fill in unset or empty environment variables** from `.env` (do not overwrite existing values)
- If required environment variables are missing, **fail fast with a clear error** (e.g., `RuntimeError`) at an early stage.

---

## External Dependencies (Network/Tools) and Failure Handling
- Treat external dependencies as "things that can fail" and provide error messages that tell the user what to do next.
- Common examples:
  - DNS resolution failure for Foundry endpoints (possibly due to private networking / private DNS)
  - Model deployment name mismatch (`FOUNDRY_MODEL`)
  - Hosted Web Search with unconfigured Bing connection
  - `npx` unavailable in the runtime environment / network restrictions for MCP tools

---

## Documentation Accuracy (Maintenance)
- When documenting Agent Framework API names/signatures/behavior:
  - Reference primary sources from Microsoft Learn and include the URL.
  - However, since **there may be discrepancies between the docs and the pinned version**, prioritize this repo's behavior (example code) when discrepancies are suspected, and leave a note.

---

## Change Guidelines (Guardrails for Autonomous Execution)
- Start with the smallest change that fulfills the objective. Avoid unnecessary refactoring, formatting, or dependency additions.
- For large modifications, briefly present the following before starting implementation:
  1) Reason for the change
  2) Design proposal
  3) Scope of impact
  4) Test/validation plan
- When adding new dependencies, first explain the necessity and alternatives (standard library / existing dependencies).

---

## Minimum Validation (Aligned with This Repo's Current State)
- Always pass the Python syntax check:
  - `python3 -m compileall -q src entities`
- If the change affects a workshop exercise, run the corresponding script to confirm there are no regressions.
