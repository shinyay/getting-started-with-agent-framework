# Demo 7 Option: Spec-driven Multi-Agent Workflow (Copilot Agent mode Prompt)

This document is an instruction document (prompt packet) for **GitHub Copilot Agent mode** to perform **Spec-driven development** in the `shinyay/getting-started-with-agent-framework` repository.
The goal is to compose multiple agents (Constitution → Specify → Plan → Tasks) as a **Workflow** and implement them in a form that can be executed from both a CLI demo and a DevUI entity.

## How to use (Success criteria included)

1. Open Copilot Agent mode
   - Success criteria: Agent mode is available and the repository is open

2. **Paste the "Copilot Agent Mode Instructions" below as-is**
   - Success criteria: Copilot understands the premise of "investigating existing code in this repo before proceeding"

3. Additionally, paste your development theme (requirements) for this session
   - Success criteria: Copilot lists missing information as questions and does not fill in with guesses

4. (Additional requirement) Verify that when running the CLI demo with no arguments, application requirements can be entered via standard input
  - Success criteria: Running without arguments displays an interactive prompt, and the entered content is used directly as the workflow's initial prompt

---

## Copilot Agent Mode Instructions (For Pasting)

You will implement a new multi-agent workflow for **Spec-driven development** in this repository (`shinyay/getting-started-with-agent-framework`), similar to `src/demo5_workflow_edges.py`.
However, what you are building this time is a workflow that can generate four stages—"Constitution / Specification / Technical Plan / Task list"—using multiple agents. Please create both a CLI demo and a DevUI entity.

### 1) Mandatory Constraints (Important)

- This repo has **pinned** dependencies in `requirements.txt` (including `--pre`).
  **Do not write APIs based on guesswork**. There may be differences from the latest documentation, so always **base your work on the existing implementations in this repo (`src/demo*.py`, `entities/**`)**.
- Handle .env the same way as existing demos:
  Since env variables may be injected as empty strings in Dev Container / Codespaces, **load .env from the repo root and only fill in unset or empty env variables** (do not overwrite existing values).
- Do not expose Secrets/Keys in code, logs, or documentation.
- After changes, at minimum `python3 -m compileall -q src entities` must pass.

### 2) What to Add (Deliverables and Features)

#### A. Multi-Agent Workflow (4 Stages)

The order is fixed:
1. **Constitution Agent** (Project Constitution)
2. **Specify Agent** (Requirements Clarification / Functional Specification)
3. **Plan Agent** (Technical Plan / Data Model / Design)
4. **Tasks Agent** (Actionable Task Breakdown)

#### B. Artifacts Must Always Be Generated in "English + Japanese"

Artifacts should be output as separate files (to avoid readability issues from mixing languages).
The following 8 files are expected, with mandatory headings fixed for each file:

- `artifacts/constitution.en.md`
- `artifacts/constitution.ja.md`
  Mandatory headings (English version):
  - `## Principles`
  - `## Prohibitions`
  - `## Definition of Done`
  - `## Security & Secrets`
  - `## Output Format Rules`
  Mandatory headings (Japanese version—no variation allowed):
  - `## Principles [JP: Gensoku]`
  - `## Prohibitions [JP: Kinshi Jikou]`
  - `## Definition of Done (DoD) [JP: Kanryou no Teigi]`
  - `## Security & Secrets [JP: Security to Secrets]`
  - `## Output Format Rules [JP: Shutsuryoku Format Kiyaku]`

- `artifacts/spec.en.md`
- `artifacts/spec.ja.md`
  Mandatory headings (English version):
  - `## Goal`
  - `## Scope`
  - `## Requirements`
  - `## Non-Goals`
  - `## Edge Cases`
  - `## Acceptance Criteria`
  Mandatory headings (Japanese version—no variation allowed):
  - `## Goal [JP: Gooru]`
  - `## Scope [JP: Sukoopu]`
  - `## Requirements [JP: Youken]`
  - `## Non-Goals [JP: Hi-Gooru]`
  - `## Edge Cases [JP: Ejji Keesu]`
  - `## Acceptance Criteria [JP: Ukeire Kijun]`

- `artifacts/plan.en.md`
- `artifacts/plan.ja.md`
  Mandatory headings (English version):
  - `## Approach`
  - `## Files to Change`
  - `## Implementation Steps`
  - `## Data Model`
  - `## Risks`
  - `## Validation`
  Mandatory headings (Japanese version—no variation allowed):
  - `## Approach [JP: Apuroochi]`
  - `## Files to Change [JP: Henkou suru File]`
  - `## Implementation Steps [JP: Jissou Tejun]`
  - `## Data Model [JP: Deeta Moderu]`
  - `## Risks [JP: Risuku]`
  - `## Validation [JP: Kenshou]`

- `artifacts/tasks.en.md`
- `artifacts/tasks.ja.md`
  Mandatory heading: `## Task List` (checkbox format)
  Rule: **1 task = 1 logical change**; each task must include `Files` / `Done when` / `Validate with` (the Japanese version should list the corresponding items in Japanese).

  Mandatory heading (Japanese version—no variation allowed): `## Task List [JP: Tasuku Risuto]` (checkbox format)
  Rule: **1 task = 1 logical change**; each task must include `Target Files [JP: Taishou File]` / `Completion Criteria [JP: Kanryou Jouken]` / `Validation Method [JP: Kenshou Houhou]`.

Important: Artifact content should be generated based on user input (described below). Missing information should be listed as "questions" and **not filled in with guesses**.

##### Additional Guardrails (Points That Commonly Cause Issues in Implementation)

LLMs sometimes **fail to follow the output format (EN/JA separation)** even when instructed.
Even in such cases, having the CLI/DevUI implementation crash and produce no artifacts is unacceptable, so the following "resilience" requirements are explicitly added:

- **Output Format Contract (Instructions to the LLM)**
  - EN/JA must always be separated using the following markers, with **no text outside the markers**:
    - `<!-- BEGIN EN --> ... <!-- END EN -->`
    - `<!-- BEGIN JA --> ... <!-- END JA -->`
  - Each language block must include all specified mandatory headings (`## ...`).
  - Unclear points should be listed under "Open Questions/Unresolved Questions" and not filled in with guesses.
  - **Open Questions are only allowed as an additional heading at the end** (e.g., `## Open Questions` / `## Unresolved Questions [JP: Mikaiketsu no Shitsumon]`).
    - Additional headings are OK, but **mandatory headings must not be removed**.

- **Implementation-Side Robustness (Most Important)**
  - **Strict parsing success criteria (if not met, fall back entirely)**:
    - **Both** EN/JA markers are present
    - Each language block contains **all mandatory headings** for that artifact
    - No extraneous text outside the markers (no contract violations)
  - Even if the above are not met (e.g., markers are missing / one of EN/JA is missing / mandatory headings are incomplete / extraneous text outside markers), the
    **CLI must not crash and must always write out all 8 files**.
  - During this fallback, "do not fabricate translations":
    - Example: In both EN/JA files, save the **original output as-is** under `## Raw Output` (Japanese version: `## Original Output (Raw Output) [JP: Moto no Shutsuryoku]`),
      and add placeholders for mandatory headings (e.g., "Please re-run to generate").
  - In other words, use a two-tier approach: "strict parsing (success)" and "fallback (non-crash)."

  - Additional implementation note: The shape of event/completion data is not always consistent.
    - For each stage's result, use `.text` if available; otherwise, stringify with `str(...)` and save as Raw Output.

#### C. DevUI Support (Required)

Add a new entity under `entities/` so it can be launched from DevUI.
Model it after `entities/event_planning_workflow/workflow.py`, using the `WorkflowBuilder.register_agent(...)` pattern to compose it.

DevUI requirements:
- The entity must not crash on import (do not break the "listing" even if env is not set)
- Processing that requires env should **fail-fast inside the agent creation function**
- Set `output_response=True` on the final executor (Tasks) so the DevUI final output is clearly displayed

#### D. CLI Demo (Required)

Add a new demo under `src/` (filename should follow existing naming, e.g., `demo7_spec_driven_workflow.py`).
Follow the pattern from `src/demo5_workflow_edges.py`:

- `AzureCliCredential` + `AzureAIAgentClient(...).as_agent(...)`
- `AsyncExitStack` for managing the lifetime of credential/client/agent together
- Use `workflow.run_stream(prompt)` and branch on event types to display progress
- **Collect results "per executor_id"** for each stage, and display them together at the end
  (treat the final output event as a fallback)

Additional requirements (pitfall prevention for implementation):
- **Do not crash on artifact parse failure** (satisfy the "implementation-side robustness" described above).
  - Even if markers are not followed, do not raise `ValueError` or similar; save using the fallback instead.
- **Do not guess technology choices such as web frameworks**.
  - Example: Guessing "looks like Flask/FastAPI" is prohibited. Provide evidence for technology choices from `requirements.txt` / repo implementations;
    if no evidence exists, state "TBD (align with existing repo implementation)."

Additional requirements (interactive input):
- When the CLI demo is **run without arguments**, it should accept input via standard input (stdin) for "what kind of application you want to build."
- Use that stdin input (multi-line allowed) as the **initial prompt for the Spec-driven workflow (a requirements statement including project/context/requirements/constraints)**, running Constitution → Specify → Plan → Tasks.
- Implementation notes:
  - Interactive mode should only be active when `sys.stdin.isatty()`, to prevent hanging in pipes or CI.
  - Multi-line input ends with **an empty line (Enter only)** (TTY assumed).
  - If no input is provided, fail-fast with a clear error message.
  - If a prompt is passed via arguments (e.g., `--prompt` / `--file`), do not prompt via stdin.

### 3) Agent Roles (Instruction Requirements)

The instructions passed to each agent must satisfy the following:

- **Constitution Agent**
  - Purpose: Define judgment criteria for this project (principles, prohibitions, DoD, security, output format rules)
  - Output: `constitution.*.md` only
  - List unclear points as "Open Questions" and do not make assumptions

- **Specify Agent**
  - Purpose: Translate user requirements into "implementable specifications" (make acceptance criteria concrete)
  - Output: `spec.*.md`
  - When specs reference external SDKs/APIs, base them on this repo's pinned implementations

- **Plan Agent**
  - Purpose: Create a technical plan from the spec (files to change, data model, implementation steps, risks, validation)
  - Output: `plan.*.md`
  - Write plans assuming "patterns that work in this repo" (src and entities)

- **Tasks Agent**
  - Purpose: Break down into PR-sized tasks (with checkable completion criteria)
  - Output: `tasks.*.md`

### 4) Tool and External Dependency Policy (Defaults for This Exercise)

- By default, **do not use Web Search** (to avoid adding environment dependencies like Bing connections).
- MCP (`npx`) is also **not required**. A proposal to add it only to the Plan Agent later is acceptable.
- In other words, the default for this exercise focuses on "Foundry Agents + 4 agents + workflow edges + artifact generation."

### 5) Environment Variables (Foundry Agents Assumed)

Minimum required:
- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`

Following existing demos:
- Load .env from the repo root (only fill in unset/empty env variables)
- If possible, add a DNS resolution check for `AZURE_AI_PROJECT_ENDPOINT` with an error message that helps distinguish Private DNS issues
  (but check at runtime, not at DevUI import time)

### 6) Workflow I/O (User Input)

The workflow input (prompt) should accept at minimum the following:

- Project: `<project name>`
- Context: `<background>`
- Requirements: `<what to build>`
- Constraints: `<languages, frameworks, runtime, non-functional>`
- Repo constraints: "pinned agent-framework; no guessing APIs; compileall required"

Additional requirements (input paths):
- When the CLI demo is run "without arguments," receive the above input **interactively from stdin**.
- If possible, adopt one of the following for ease of user input:
  - A single free-text entry (subsequent agents will structure it)
  - Or a simple wizard that asks for Project/Context/Requirements/Constraints in sequence

If input is insufficient, have Constitution/Specify produce a list of questions and include those questions in the artifacts.

### 7) Acceptance Criteria

- The CLI demo starts and all 4 stages execute in sequence (assuming env is set up)
- When the CLI demo is run without arguments, it proceeds from stdin input to workflow execution (interactive only with TTY; does not hang on non-TTY)
- The DevUI entity can be imported and appears in the DevUI listing (does not crash even if env is not set)
- `artifacts/*.md` are generated in both English and Japanese, satisfying the mandatory headings
- **(Additional)** Even if the LLM violates EN/JA markers or heading rules, the CLI does not crash; it generates all 8 files with Raw Output + placeholders so content is traceable
- `python3 -m compileall -q src entities` passes

### 8) How to Proceed (Requirements for Copilot)

- First, verify APIs based on `requirements.txt` and existing files (`src/demo5_workflow_edges.py`, `entities/event_planning_workflow/workflow.py`, `src/demo6_devui.py`) before starting implementation.
- Since `WorkflowBuilder` may have pinned version differences, consider compatibility as in existing demos (e.g., fallbacks when kwargs do not match).
- Do not make unnecessary refactors or add dependencies (minimum changes only).

---

## Optional: Input template (paste after the instructions)

Project:
- Name:
- Audience:
- Timeline:

Context:
- Background:
- Existing system / repo constraints:

Requirements:
- Must-have:
- Nice-to-have:

Constraints:
- Language/runtime:
- Deployment:
- Security/compliance:

Open questions:
- (If any)
