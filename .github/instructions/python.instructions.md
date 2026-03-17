---
applyTo: "**/*.py"
---

# Python path-specific instructions

These are guidelines for Copilot to maintain consistent quality, executability, and reproducibility for Python implementations in this workspace (primarily `src/` and `entities/`).

## Code Quality / Style
- Public APIs (functions/classes imported by other modules) **must have type hints** (at minimum for arguments and return values).
  - Example: do not omit `-> None` / `-> str` / `-> dict[str, str]`, etc.
- For asynchronous I/O (Agent Framework's `run`/`run_stream`, Azure credential/client, etc.), **do not break the `async`/`await` pattern**.
  - Use `async with` for `azure.identity.aio.AzureCliCredential`
  - Also guarantee cleanup of `AzureAIAgentClient` / `agent` with `async with`
- Do not swallow exceptions.
  - However, for failures from external dependencies (Foundry / Bing / MCP / DNS / npx, etc.), fail fast with `RuntimeError` or similar, **including guidance on what to check** so the user can take the next step
  - Preserve the original exception with `raise ... from ex`

## "Executable" Implementation Conventions for This Repository (Important)
- Write code assuming dependencies are pinned (check `requirements.txt`).
- For agent creation, prefer **`AzureAIAgentClient(...).as_agent(...)`** by default and do not replace APIs based on guesswork.
  - If there are differences from doc examples, first align with the examples in the repository (`src/demo*.py`)
- Scripts should follow the basic pattern of `async def main() -> None:` + `if __name__ == "__main__": asyncio.run(main())`.

## .env / Environment Variable Handling (Dev Container / Codespaces Considerations)
- Never expose Secrets/Keys in code or logs.
- In Dev Container / Codespaces, environment variables may be **injected as empty strings**, so the following is recommended:
  - **Explicitly load** the `.env` file from the repository root
  - **Only fill in unset or empty environment variables** from `.env` (do not overwrite existing values)
- Align the implementation with this repo's existing pattern (`dotenv_values` + fill-only).

## External Dependency Boundaries (I/O Isolation)
- Keep tools/integrations "small with clear boundaries."
  - Localize call sites for external APIs / HTTP / MCP / subprocess / FS, etc.
  - Example: extract DNS pre-checks, `npx` existence checks, and Bing connection configuration assembly into small functions
- Be conservative when adding new dependencies.
  - If additions are needed, compare with alternatives (standard library / existing dependencies) and provide reasoning

## Structured Output (When Needed)
- When possible, **structure** results used in UI / Workflows.
  - Use `pydantic.BaseModel` and receive with `response_format=<Model>`
- If `response.value` may be empty due to runtime environment differences, consider a fallback that recovers from `response.text` (align with existing exercise code implementations).

## Streaming
- For UIs/CLIs that require incremental display, prefer `run_stream()`.
- Since streaming result display may encounter SDK event shape differences:
  - Provide a resilient display path such as collecting completion events or falling back to final output

## Testing Guidelines (When Introducing Tests)
- Confine external calls (Azure/Foundry/MCP/HTTP) to a mockable layer.
- Handle "prompt changes" with evaluation/golden tests (snapshots, etc.) rather than strict unit test matching.
  - However, if this repo has no test infrastructure, discuss the adoption plan before adding one

## Minimum Checks
- After changes, at least pass the Python syntax check:
  - `python3 -m compileall -q src entities`
