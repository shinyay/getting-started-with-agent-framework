# GitHub Copilot Repository Instructions

## Purpose of This Repository
- Implement and validate AI Agents and Workflows using Python with Microsoft Agent Framework.
- **Do not write based on guesswork** (Agent Framework updates frequently, so API accuracy is the top priority).
- The highest priority is "it actually works with the pinned versions in this repository."

---

## Accuracy (Version Tracking) Rules
- Always check dependency versions before making changes or implementing.
  - First check `requirements.txt` / `requirements*.txt`
  - Also check `pyproject.toml` if it exists
- When explaining or implementing Agent Framework APIs/behavior, **verify against primary sources**.
  - Reference the Microsoft Learn API Reference / User Guide
  - However, since **there may be discrepancies between the docs and the pinned version**, prioritize this repository's implementation and examples when they conflict with doc examples
- If there are unknowns or suspected spec changes, do not implement based on guesswork. Provide evidence (docs / release notes / measured logs / existing implementation).

---

## Agent Framework Implementation Policy (Python / Defaults for This Repo)
- Authentication defaults to **Entra ID (Azure CLI credential)** (assumes `az login`).
- For agent creation, follow this repository's pattern (e.g., `AzureAIAgentClient(...).as_agent(...)`) and do not arbitrarily replace APIs.
- Implement `run()` / `run_stream()` assuming async.
  - Prefer streaming for CLI/DevUI and other UIs (but if there are SDK discrepancies, prioritize "a working form" above all)
- Implement tools in "small, low-side-effect" units, and add type hints and descriptions so the meaning of arguments is clear.
  - Where possible, use `typing.Annotated` with descriptions (e.g., Pydantic's Field, etc.)

---

## Environment Variables / .env Handling
- Never expose Secrets/Keys in code or logs.
- Update `.env.example` as needed so users can configure settings (do not include actual values).
- In Dev Container / Codespaces, environment variables may be **injected as empty strings**, so:
  - Prefer the approach of explicitly loading the `.env` from the repository root and **only filling in unset or empty environment variables**
  - Do not unconditionally overwrite existing values (do not interfere with temporary overrides like `VAR=... python ...`)

---

## Repository Structure (Recommended)
- Place implementations under `src/`.
- Extract "externally dependent operations" (LLM calls, MCP, web search, etc.) to make testing and swapping easier.

---

## How to Propose Changes (Copilot Behavior)
- First, propose the smallest change that fulfills the objective.
- For large modifications, briefly present the following before starting implementation:
  1) Reason for the change
  2) Design proposal
  3) Scope of impact
  4) Test plan
- When adding new dependencies, first explain the necessity and alternatives (standard library / existing dependencies).

---

## Minimum Post-Change Checks (Aligned with This Repo's Current State)
- Always pass the Python syntax check first:
  - `python3 -m compileall -q src entities`
- If the change affects an exercise/script, run the corresponding script to confirm there are no regressions.
- Proposals to introduce lint/type/test tooling are welcome, but do so **minimally in line with the existing development flow** (do not assume tools that have not been adopted).

---

## GitHub Pages (workshop-pages-theme)

This repo uses `remote_theme: shinyay/workshop-pages-theme` for GitHub Pages.

### Page Layout Rules
- `layout: workshop` → `index.md` (landing page only)
- `layout: step` → Exercise READMEs. Requires `step_number` (int) and `permalink: /steps/N/`
- `layout: cheatsheet` → Demo walkthroughs. Requires `parent_step` (int) and `permalink: /cheatsheet/N/`

### Content Rules
- Use GitHub callout syntax: `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`, `> [!IMPORTANT]`
- Fenced code blocks must have language identifiers (```python, ```bash)
- Do NOT modify the `_config.yml` `exclude` list without understanding Jekyll build implications
- Steps auto-discovered via layout + step_number; no manual linking needed
