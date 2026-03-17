---
applyTo: "**/*.md"
---

# Documentation path-specific instructions

These are rules for Markdown in this repository (`README.md` / `demo/*.md` / future `docs/**`, etc.)
that prioritize **accuracy** and **maintainability** above all.

## 1) Verifying and Citing Primary Sources (Most Important)
- When documenting Agent Framework **API names / signatures / return values / event names / exceptions / behavior**, always consult primary sources.
  - By default: the relevant Microsoft Learn page (API reference / user guide)
  - Also include: the **reference URL** (and section heading if possible)
- If the docs only provide "conceptual explanations" and the API specification is ambiguous, the following may also be used as evidence:
  - Implementations and examples within this repository (`src/demo*.py` / `entities/**`)
  - The pinned version in `requirements.txt` (e.g., `agent-framework==...`)

## 2) Handling Pinned Versions vs. "latest"
- This repository **pins** agent-framework* in `requirements.txt`.
  - Documentation should **be based on what works with the pinned version** by default.
- If a Microsoft Learn reference refers to "latest", explicitly state the following in the text:
  - "This page may reflect the latest version"
  - "There may be differences with the pinned version used in this repository"
  - If discrepancies are suspected, **prioritize the behavior of this repository's code** and add a note as needed

## 3) Writing Procedural Guides (Reproducibility)
- Write procedures on a **per-command basis** (one step = one purpose).
- Always attach **success criteria** to each step:
  - Example of expected output, or a verification method (e.g., `/health` returns 200, a specific log message appears, etc.)
- Explicitly document failure scenarios as "common pitfalls" (network/DNS/permissions/unset env vars, etc.).

## 4) Documenting Environment Variables and Secrets
- Never include secrets/keys in documentation.
- For env vars, document the "name," "purpose," and "example (placeholder)."
- Since **empty string env injection** can occur in Dev Container / Codespaces:
  - Write documentation assuming the approach of explicitly loading `.env` and only filling in unset/empty values (this repo's implementation policy).

## 5) Writing for Resilience to Change (Maintenance)
- Separate stable facts (pinned version / file paths / env var names) from volatile facts (portal UI / execution output content).
- For volatile sections, explicitly label them as "example" or "reference" and avoid making definitive statements.
- Include "where to look first if this document becomes outdated":
  - `requirements.txt` (pinned version)
  - `src/demo*.py` (working examples)

## 6) Prohibited Practices
- Do not make definitive statements about API specifications without verification.
- Do not leave "probably/maybe" statements without supporting evidence (either add evidence or remove the statement).
