# Agent Framework Learning Guide (Demo 1–6: Code Reading Edition)

This `demo/guide.md` is a guide focused not on "how to run things" but on **what a newcomer to Agent Framework development should take away from the demo code and how to apply it**.

- The "task" is **reading code** (Demos 1–6 are designed so that concepts build incrementally)
- Agent Framework updates rapidly, so **the pinned dependencies in this repository** and **the implementations in `src/demo*.py`** are the source of truth

  - Checking the pinned version: `requirements.txt` (e.g., `agent-framework==1.0.0b260123`)

> Microsoft Learn may reflect the "latest" version. If discrepancies are suspected, prioritize the behavior of this repository's pinned version (`requirements.txt` / `src/` / `entities/`).

---

## Recommended Reading Order (Learning Roadmap)

| Demo | Theme to Learn | Primary File |
|---:|---|---|
| 1 | Minimal agent execution, env var/network fail-fast, async resource management | `src/demo1_run_agent.py` |
| 2 | Hosted tool (Web Search) integration and handling "connection info" | `src/demo2_web_search.py` |
| 3 | MCP (stdio) = making external processes into tools, environment dependencies/safety | `src/demo3_hosted_mcp.py` |
| 4 | Structured output (Pydantic), `response_format` and fallback design | `src/demo4_structured_output.py` |
| 5 | Orchestration with Workflows, event-driven observation, lifetime management | `src/demo5_workflow_edges.py` |
| 6 | DevUI hosting, entity/workflow discovery and UX design (separating import and runtime validation) | `src/demo6_devui.py`, `entities/**` |

---

## Common Patterns Across This Repository

### 1) `.env` Is **fill-only** (Only Fills Unset/Empty Values)

Each demo explicitly loads `.env` from the repository root (`/workspaces/.env`), but **does not unconditionally overwrite existing environment variables**.

- In Dev Container / Codespaces, env may be **injected as empty strings**
- Does not interfere with temporary overrides like `VAR=... python ...` during debugging

This policy aligns with the `AGENTS.md` guideline: "Only fill unset/empty env variables."

### 2) `_require_env()` Establishes "What Is Missing" Up Front

Since there are many external dependencies (authentication, RBAC, networking, model names, connection settings),
**determine "what is missing" before calling the SDK** and make errors easy to read.

> A common pitfall for beginners is "the SDK fails deep inside when configuration is missing, obscuring the root cause."

### 3) DNS Pre-Check (Distinguishing Private Link/Private DNS Issues)

Check whether the hostname of `AZURE_AI_PROJECT_ENDPOINT` is resolvable via `socket.getaddrinfo(...)`
to **identify network issues early**.

### 4) `async with` Ensures Credential/Client/Agent Are Properly Closed

`AzureCliCredential` and `AzureAIAgentClient`, along with agent instances, are **async resources**.
Demos consistently manage their lifetimes using `async with` (or `AsyncExitStack`).

### 5) Translate Only Exceptions You Understand

For cloud-originated exceptions like `ServiceResponseException`, only translate causes that follow typical patterns (e.g., model deployment name)
into messages that clarify **what to check next**.

### 6) Observability Is Optional (Use OpenTelemetry If Available)

Rather than making OpenTelemetry mandatory, demos enable it so that "agent/tool behavior is visible" when it is installed.
Making "convenient but environment-dependent" features **optional** is a considerate approach for demos.

### 7) Treat Ctrl+C as an "Expected Termination" (Exit Code 130)

A convention for clearly handling user interrupts in long-running processes (such as DevUI).

---

## Demo 1: Minimal Agent Execution (= Foundation for Everything After)

Target: `src/demo1_run_agent.py`

This file is not just about "running things as quickly as possible." It is the minimal form of a
common template (fail-fast + lifetime management + observability) that **clears the "failure-prone landmines" of cloud integration upfront**.

### Reading Order for This File (A Route That Avoids Getting Lost)

1. `.env` loading (fill-only)
   - Read `.env` from the repository root with `dotenv_values(...)` and fill `os.environ` with **only unset/empty values**
2. `_require_env(...)`
   - **Stop immediately** if required settings are missing (pinpoint the cause upfront)
3. `_check_project_endpoint_dns()`
   - Determine whether the Azure AI Foundry project endpoint host can be **resolved via DNS** "before connecting"
4. (Optional) OpenTelemetry initialization
   - If the environment supports import, observe spans as a single-line log (skip if not available)
5. `main()`
   - Use `async with` to manage credential/agent lifetimes, then `agent.run()` → `result.text`

### 1) `.env` Is Fill-Only: Handling "Empty String Env" in Dev Container/Codespaces

`_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"` loads `.env` from the repository root.

The key point here is **not unconditionally overwriting** with `.env` values.

- In Dev Container / Codespaces, env may be **injected as empty strings** ("the variable exists but is empty")
- Does not interfere with **temporary overrides** like `VAR=... python ...` during debugging

The implementation fills the `.env` value only when the existing value is `None` (unset) or `strip()` returns empty.

### 2) `_require_env(name)`: Pinpoint Failures "Up Front," Not "Deep Inside"

`_require_env(...)` is not just input validation; it is a function designed to **make failures fast and readable**.

In Demo 1, the minimum requirements are:

- `AZURE_AI_PROJECT_ENDPOINT` (Azure AI Foundry project endpoint)
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` (model deployment name in the Azure AI Foundry project)

Rather than "failing vaguely" after calling the SDK, pinpointing "what is missing" before the SDK call
**drastically reduces the investigation cost for beginners**.

### 3) `_check_project_endpoint_dns()`: Distinguish Network Issues "Before Authentication"

Parse `AZURE_AI_PROJECT_ENDPOINT` as a URL and use `socket.getaddrinfo(host, 443)` to check **DNS resolution only**.
In other words, this check does not verify TCP/HTTPS connectivity but provides early differentiation for:

- The endpoint is malformed as a URL (host cannot be extracted)
- A private networking / private DNS endpoint is being accessed from an environment that cannot resolve the name

In cloud development, before suspecting "RBAC? Auth? SDK?...", simply establishing that **"DNS is not working"** is highly effective.

### 4) Why `async with` Is "the Standard Pattern in This Repo"

`AzureCliCredential` (aio version) and agents are treated as **async resources** and closed properly with `async with`.

- `async with AzureCliCredential() as cred:`
- `async with AzureAIAgentClient(credential=cred).as_agent(...) as agent:`

Even though demos are short, proper lifecycle management pays off increasingly in later stages (workflow / DevUI) for "forgotten closes" and "cleanup during exceptions."

> Note: `AzureCliCredential` relies on "Azure CLI login state," so if you are not logged in or lack permissions, failures will occur from this point on.

### 5) `agent.run(...)` and `result.text`: Starting with "Understanding as a String" Is the Right Approach

Demo 1 does not structure the response; it simply displays `result.text` to create a minimal success experience.

- First, lower the learning cost with the experience of "getting a response"
- Then, notice that "strings are hard to work with" → naturally leads to Demo 4 (Structured Output)

### 6) Observability Is Optional: If OpenTelemetry Is Available, See Behavior in Single-Line Logs

The `try/except` around `configure_otel_providers` at the top is an important design consideration for demos.

- Works even in environments without OpenTelemetry (not mandatory)
- When installed, `_DemoSpanExporter` picks up only agent/tool-like spans and outputs them as readable single-line logs

### For Practical Application (Mapping to Real Development)

- "I want to add tools" → Demo 2/3
- "I want to handle output programmatically" → Demo 4
- "I want to split into multiple stages" → Demo 5

---

## Demo 2: Hosted Web Search (Treating Tools as "Design Elements")

Target: `src/demo2_web_search.py`

This file inherits the foundation from Demo 1 (fill-only `.env` / `_require_env` / DNS preflight / `async with`) and
demonstrates **where you get stuck and how to design for easy debugging** when "adding a Hosted tool as an agent capability."

### Reading Order for This File (A Route That Avoids Getting Lost)

1. `.env` loading (fill-only)
   - Same as Demo 1: fill from `.env` only for unset/empty values
2. `_require_env(...)` and `_check_project_endpoint_dns()`
   - Establish Azure AI Foundry project endpoint prerequisites upfront (including DNS differentiation)
3. `_get_bing_tool_properties()`
   - Assemble **connection info (Bing grounding / Custom Search)** from env for Hosted Web Search
4. `HostedWebSearchTool(additional_properties=...)`
   - Pass user_location + Bing connection info to the tool
5. `try/except ServiceResponseException`
   - Translate typical failures (model resolution failure) into messages that point to "what to check next"

### 1) `_get_bing_tool_properties()`: Absorb Env Name Variations and Fix "Connection Prerequisites"

Hosted Web Search does not simply "call Bing" but rather uses Azure AI Foundry's hosted web search (Bing grounding),
which requires a **connection (project connection ID) created in the Azure AI Foundry project**.

This demo uses `_get_bing_tool_properties()` to absorb environment variable naming variations.

- Env names the library tends to reference (from error messages):
  - `BING_CONNECTION_ID`
  - `BING_CUSTOM_CONNECTION_ID`
  - `BING_CUSTOM_INSTANCE_NAME`
- Env names commonly seen in Azure AI Foundry documentation and UI:
  - `BING_PROJECT_CONNECTION_ID`
  - `BING_CUSTOM_SEARCH_PROJECT_CONNECTION_ID`
  - `BING_CUSTOM_SEARCH_INSTANCE_NAME`

Furthermore, it separates use cases into two categories and makes it clear in code "which should be set":

- Standard (Bing grounding)
  - Only `connection_id` is needed (returns `{"connection_id": ...}`)
- Custom Bing Search
  - **Both** `custom_connection_id` and `custom_instance_name` are required

> Important: The trap for beginners is that this is not an "API key."
> What is needed is the connection ID (project connection) created in the Azure AI Foundry portal.

### 2) `additional_properties`: Pass "Context" and "Connection" for Tool Execution in the Same Place

Tool configuration is consolidated in `HostedWebSearchTool(additional_properties={...})`.

- `user_location`: Localization context for search results (e.g., Seattle / US)
- `**bing_props`: Connection info returned by `_get_bing_tool_properties()`

By structuring it this way,
"improving search accuracy (= adding context)" and "fixing connections (= fixing the connection)"
can be **tracked in the same configuration block**, making it harder for beginners to lose track of changes.

### 3) `ServiceResponseException` Translation: Make Model Resolution Failure "Fixable in the Shortest Time"

The `agent.run(...)` call is wrapped in `try/except ServiceResponseException`,
and when `"Failed to resolve model info"` is found, it is translated into a `RuntimeError`.

The two design intentions communicated here are:

1. **For typical failures, present the action the reader should take next**
   - Check `Models + endpoints` in the Azure AI Foundry portal, etc.
2. Clearly warn about "deployment name confusion"
   - `AZURE_AI_MODEL_DEPLOYMENT_NAME` is the **model deployment name in the Azure AI Foundry project**
   - It is easily confused with Azure OpenAI's deployment name (which may be used in a different project/SDK)

> Note: The exception message displays the current value of `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
> This is for identifying "configuration mix-ups" rather than being a secret, but be cautious if you do not want it in logs.

### For Practical Application (Mapping to Real Development)

- "I want to add multiple tools / also use external processes" → Demo 3 (MCP)
- "I want to structure search results for UI/DB" → Demo 4 (Structured Output)

---

## Demo 3: Hosted MCP (Making External Processes into Tools via stdio)

Target: `src/demo3_hosted_mcp.py`

This file maintains the "foundation for safely running Azure AI Foundry Agents" from Demo 2 and
is a demo for learning the concepts needed (dependency isolation / early failure / boundary awareness) when the tool's implementation is **an external process rather than a Python function**.

### Reading Order for This File (A Route That Avoids Getting Lost)

1. `.env` loading (fill-only)
   - Same as Demo 1/2
2. `_require_env(...)` and `_check_project_endpoint_dns()`
   - Establish Azure AI Foundry-side prerequisites upfront (endpoint / model deployment / DNS)
3. `_require_command("npx")`
   - Fail-fast on local dependencies needed for MCP server startup (Node.js / npx)
4. `MCPStdioTool(...)` definition
   - How to start the tool (= external process) and align it toward the safe side
5. `client.as_agent(..., tools=[...])` → `agent.run(...)`
   - Grant the tool as a "capability" to the agent and execute
6. `try/except ServiceResponseException`
   - Make typical cloud-side errors (model resolution failure) more readable

### 1) `_require_command("npx")`: Distinguish External Dependencies "Before Connecting"

`_require_command` uses `shutil.which(cmd)` to check PATH and stops with a clear message if `npx` is not found.

The key point of Demo 3 is that before "can I connect to Azure AI Foundry?",
there can be **failures dependent on the local environment (Node/npx not installed)**.

Adding this check allows quick identification of whether the failure is at:

- Azure (authentication/RBAC/model name)
- Network (DNS/Private Link)
- Local (Node/npx/package retrieval)

### 2) `MCPStdioTool(...)`: When the Tool "Becomes an External Process," Boundaries Increase

The tool in Demo 3 is configured as:

- `command="npx"`
- `args=["-y", "@modelcontextprotocol/server-sequential-thinking"]`
- `name="sequential-thinking"`
- `load_prompts=False`

The important point here is that tool invocation is no longer a Python function call but
**communication with an external process via standard I/O (stdio)**.

This means failure modes increase:

- `npx` is not found (PATH)
- External package retrieval fails (network restrictions)
- The external process starts but does not respond with the expected protocol

This demo accounts for such "environmental factors" and adds the minimum guard (`_require_command`).

### 3) `args=["-y", ...]`: Prevent Interactive Prompts from Halting Execution (For CI/DevContainer)

`npx` may display a confirmation prompt depending on the situation,
so `-y` is added to ensure it **runs non-interactively**.

(For demos, "it must work" is the top priority, so these kinds of options are quietly important.)

### 4) `load_prompts=False`: Fix Behavior and Improve "Explainability"

`load_prompts=False` disables automatic loading of prompts from the external tool.

For a demo, this has the following significance:

- Agent behavior is less likely to fluctuate due to environment or tool implementation differences
- It is easier to explain: "the prompt for this demo is defined right here"
- Tool integration behavior is aligned toward the **safe (predictable) side**

### 5) "How to Use" the Tool Also Appears in Instructions

The `instructions` include a statement to the effect of
"plan your steps using the sequential-thinking tool before answering,"
specifying not just that the tool is available but **the intent for how to use it**.

For Hosted tools / MCP tools, it is not the case that "adding a tool automatically makes things better."
The key is to **design in the instructions when and why to use it**.

### 6) `ServiceResponseException` Translation: Make Cloud-Side Failures "Fixable in the Shortest Time"

The `agent.run(...)` call is wrapped in `try/except ServiceResponseException`,
and `"Failed to resolve model info"` is translated to a `RuntimeError` (same approach as Demo 2).

While MCP integration demos tend to highlight "local failures,"
cloud-side failures like **model deployment names and permissions** happen routinely too,
so the key is to make both failure modes "actionable for the reader."

### 7) Security Perspective (Minimum for Beginners)

MCP (external process invocation) inherently increases boundaries.

- Supply chain (which packages are being executed)
- Execution permissions (what can be done locally)
- I/O boundaries (what data is passed via stdio)

Keeping "which commands to allow" and "which tools to allow in production" in mind from the demo stage
makes it less likely to break down when scaling to workflows / DevUI.

---

## Demo 4: Structured Output (Turning LLM Output into "Application-Ready Data" with Pydantic)

Target: `src/demo4_structured_output.py`

This demo extends Demo 1–3 (fail-fast / tools / exception translation) by adding
the practical requirement of **"converting LLM output into a data structure usable by applications."**

> Demo 1 first shows `result.text` for the "it works" experience,
> and Demo 4 solves "it is hard to use as-is for applications" with "types."

### Reading Order for This File (A Route That Avoids Getting Lost)

1. `VenueInfoModel` / `VenueOptionsModel` (Pydantic schemas)
   - Define what you want to "structure" (= application requirements)
2. `HostedWebSearchTool(... additional_properties=...)`
   - Grant the agent the means to gather information (Web Search)
3. `client.as_agent(... instructions=...)`
   - *Design in natural language* "how to use the tool and how to respond"
4. `agent.run(..., response_format=VenueOptionsModel)`
   - The main part: receive output "as a model, not a string"
5. `response.value` → fallback (`response.text` → `model_validate_json`)
   - A resilient way to receive results that handles version/backend differences

### 1) Schema Design: Fix LLM Output into a "Storable/Displayable Format"

`VenueInfoModel` and `VenueOptionsModel` are the core of this demo.

- `VenueInfoModel` contains info for one venue
  - `title`, `description`, `services`, `address` are `str | None`
    - Information from the web may be missing, so the type is designed to "expect missing data" from the start
  - `estimated_cost_per_person: float = 0.0`
    - Items you want to treat as numbers are fixed to float, with a default for when not retrieved
- `VenueOptionsModel` is an array of venue candidates
  - `options: list[VenueInfoModel]`

The intent behind this design is to specify **"what the LLM should output" not through text alone but
by defining the "output shape" with a schema**.

> In practice, this "output shape" directly becomes DB columns or UI display fields.
> That is why placing the schema first makes subsequent implementation (storage/validation/diff comparison) much easier.

### 2) Tool Configuration: Pass Search Context (user_location) and Connection (Bing Connection) Together

Hosted Web Search is used as in Demo 2, but in Demo 4 the context is
"search and *return as structured data*" rather than "search and done."

This demo consolidates tool configuration as follows:

- In `additional_properties`:
  - `user_location` (search localization context)
  - `bing_props` (connection info; the return value of `_get_bing_tool_properties()`)

The point is that **even when discussing structured output, "connection and search context" remain important**.
If the search results are inconsistent, the output will be inconsistent even with a schema.

### 3) Instructions: Fix Not Just the Schema but the "Attitude of How to Respond"

The `instructions` in `client.as_agent(...)` are short but intentional:

- Use web search to find candidates
- Return **only structured data matching the provided schema**

Even with `response_format`, LLMs sometimes "add explanatory text."
This demo shows the design of preemptively nailing down in instructions:
"Return only structured data, not long natural language text."

### 4) `response_format=VenueOptionsModel`: Receiving Output Changes from "String" to "Model"

The call to `agent.run(...)` uses:

- `response_format=VenueOptionsModel`

This is the star of Demo 4.
On success, the return value `response` contains **the result as a Pydantic model**.

The code first checks `getattr(response, "value", None)` and then loops through `venue_options.options` for display.

Benefits of this approach:

- The application side can work with **typed data** like `option.estimated_cost_per_person`
- Downstream processing (sorting/filtering/saving) can be written as normal Python code

### 5) Fallback: Recover from `.text` When `.value` Is Missing/Unavailable

This demo's approach to "resilience" is thorough:

1. First, try `response.value`
2. If missing, check `response.text`
3. If `text` looks like JSON (`{...}`), try `VenueOptionsModel.model_validate_json(text)`

As noted in the code comments, due to environment or version differences,
"the response was supposed to be structured, but `.value` is empty and `.text` contains the JSON."

What this fallback conveys is the following practical stance:

- **Do not assume "the SDK always returns the ideal form"**
- However, do not swallow everything either; instead:
  - Display if retrieved
  - Display "what could not be retrieved" if not (`No structured data found...`)
  preserving debuggability

> When applying this, you could add retries for "not JSON" or "does not match schema,"
> or prompt modifications (e.g., strengthening "Return JSON only").

### 6) Typical Failure Mode: Make Model Resolution Failure "Fixable in the Shortest Time"

`agent.run(...)` is wrapped in `try/except ServiceResponseException`,
and `"Failed to resolve model info"` is translated to a `RuntimeError` (same approach as Demo 2/3).

Even when discussing Structured Output, the most common failure in practice is this:

- `AZURE_AI_MODEL_DEPLOYMENT_NAME` does not match the "model deployment name" in the Foundry project
- `AZURE_AI_PROJECT_ENDPOINT` points to a different project

This demo attaches current values to the error,
making it easy to identify "what to fix" in a short time.

### Security/Trust Boundary Notes (Minimum for Beginners)

When Web Search is included, input (search results) comes from external sources.
Structured Output can constrain the output *shape*,
but **it does not guarantee the correctness (truthfulness) of the content**.

- Assume "plausible but incorrect addresses/prices" may be mixed in, and design for confirmation, sourcing, and re-validation
- In production, consider:
  - Storing URLs/sources
  - Validating prices/addresses
  - Injection (instruction contamination) countermeasures when feeding tool result text directly into prompts

### For Practical Application (Mapping to Real Development)

- "I want data to feed into UI or DB" → This demo's schema design + `response_format` is the basic pattern
- "I want to pass structured data between multiple stages" → Model the output of each step in Demo 5 (Workflow) similarly

---

## Demo 5: Workflow (From "Conversation" to "Execution Flow")

Target: `src/demo5_workflow_edges.py`

This demo progresses one step beyond "running an agent once" from Demos 1–4,
covering **connecting multiple agents as "stages," executing them while observing events via streaming**.

There are three key concepts:

1. **Lifetime management** (safely closing multiple agents / clients / credentials)
2. **Design** (role separation + minimal tool assignment + fixing execution order with edges)
3. **Observation** (formatting `run_stream()` events for "UI/logging")

### Reading Order for This File (A Route That Avoids Getting Lost)

1. `_create_agent_factory()` (core of lifetime management via AsyncExitStack)
2. Agent definitions (`coordinator`, `venue`, `catering`, `budget_analyst`, `booking`)
   - Roles and tool assignment (least privilege)
3. `WorkflowBuilder` and edges (the section declaring execution flow)
4. `workflow.run_stream(...)` and event processing
   - `AgentRunUpdateEvent` / `ExecutorCompletedEvent` / `WorkflowOutputEvent`
5. `_print_result_item()` (display layer that absorbs "shape variations" in event payloads)
6. Exception translation (model resolution / 403 / CLI not logged in)

### 1) `_create_agent_factory()`: Use `AsyncExitStack` to "Close Everything Together"

Creating multiple agents quickly makes nesting `async with` painful.
This demo solves that problem with `_create_agent_factory()`.

- Create a single `stack = AsyncExitStack()`
- Register **async resources** in sequence with `enter_async_context`:
  - `AzureCliCredential()`
  - `AzureAIAgentClient(credential=cred)`
  - Agents created with `client.as_agent(...)`
- Calling `stack.aclose()` on `close()` ensures cleanup even if exceptions occur midway

Once you learn this pattern,
it extends easily to configurations like "create 10 agents for a workflow" or "add agents dynamically."

> Also important is "creating the client only once and reusing it."
> Not creating a client per agent avoids unnecessary connections/initializations.

### 2) Role Separation: Splitting into Stages Organizes Both "Prompts" and "Tools"

This demo creates 5 agents, each assigned a
**role (instructions)** and **necessary tools**.

- `coordinator`
  - The role that decides "who does what"
  - Attach `MCPStdioTool(sequential-thinking)` to encourage planning first
- `venue` / `catering`
  - Roles that use Web Search
  - `HostedWebSearchTool(... tool_properties=bing_props)`
- `budget_analyst`
  - The role that needs computation
  - `HostedCodeInterpreterTool(...)`
- `booking`
  - The role that integrates prior results into the final answer
  - No tools (= focuses on consolidating existing results)

What this structure communicates is not "having multiple agents makes things smarter" but
**splitting stages and responsibilities makes design and debugging easier**.

> When applying this, rather than "expanding what each agent can do,"
> lean toward "attaching only the tools truly needed for that stage" to avoid breakdowns.

### 3) `WorkflowBuilder` + Edges: "Declare Execution Order in Code"

The workflow body is here:

- `builder.set_start_executor(coordinator)`
- `.add_edge(coordinator, venue)`
- `.add_edge(venue, catering)`
- `.add_edge(catering, budget_analyst)`
- `.add_edge(budget_analyst, booking)`

This creates a sequential flow—
**coordinator → venue → catering → budget_analyst → booking**
—through "edge connections."

Additionally, setting an iteration limit with `builder_kwargs = {"name": ..., "max_iterations": 30}` is practical:

- LLMs occasionally get sidetracked (iterating) endlessly
- Having a "stopping mechanism" ensures incidents converge in demo/development environments

#### Consideration for Pinned Version Differences (An Attitude Beginners Should Emulate)

`WorkflowBuilder(**builder_kwargs)` has a `try/except TypeError` fallback in case it fails.
Since Agent Framework updates rapidly,
**adding compatibility guards at "fragile points" is well worth it when working with pinned versions**.

### 4) `run_stream()`: Separate "Progress" and "Results" Instead of Streaming Every Token

This demo's streaming processing is a useful reference for UI/log design:

- `events = workflow.run_stream(prompt)`
- Read events with `async for event in events:`
- Handle each event type differently:
  - `AgentRunUpdateEvent`
    - Instead of displaying every token, display `-> {executor_id}` **only when the executor switches**
    - Shows only "who is currently active"
  - `ExecutorCompletedEvent`
    - Accumulate `event.data` as `completed[event.executor_id] = event.data`
    - Enables stable display of **per-stage artifacts** later
  - `WorkflowOutputEvent`
    - Receive the final output `final_output` as a safety net

The important point here is not
"I just want the final answer" but rather
the design of **collecting and displaying per-stage artifacts**.

The value of a workflow lies in "reusing the process."
For example, it becomes easy to extend by re-running only the venue stage or updating only the budget.

### 5) `_print_result_item()`: Absorb "Shape Variations" in Event Payloads

`ExecutorCompletedEvent.data` may vary in shape depending on SDK/backend differences.
This demo separates the display layer into `_print_result_item()` to absorb common variations:

- If it comes as a list:
  - Unwrap if 1 element
  - Recursively output all if multiple
- Prefer `.text` if available
- Also handle nested forms like `.agent_response.text`
- Fall back to `print(item)` if nothing else works

Mixing "core logic" and "display/logging" in workflow event processing causes quick breakdowns.
The first tip is to prepare a "display layer" as this demo does.

### 6) Failure Modes: Separate Cloud and Local Causes for Early Termination

Demo 5 has more dependencies and therefore more failure modes.
This file addresses them in an order that "makes it easy for the reader to differentiate":

- Immediately at startup:
  - `_require_env(...)` (missing settings)
  - `_check_project_endpoint_dns()` (DNS/network)
  - `_require_command("npx")` (local dependency)
  are established upfront
- During execution, `ServiceResponseException` translates:
  - `Failed to resolve model info` (model name mix-up)
  - 403/Forbidden (RBAC/not logged in)
  - Azure CLI credential not authenticated
  into messages that clarify "what to check next"

> In a workflow, "where it failed" matters.
> That is why error messages should include not just the "cause" but the "next action."

### For Practical Application (Mapping to Real Development)

- Expanding from "sequential" to "conditional branching/merging"
  - Before adding edges, first organize the shape of artifacts in `completed` (introducing structured output is effective)
- Building a UI
  - The design of separating `AgentRunUpdateEvent` (progress) and `ExecutorCompletedEvent` (artifacts) for display can be used directly
- Improving cost/safety
  - Minimize the agents that have tools, and always add a "stopping point" like `max_iterations`

---

## Demo 6: DevUI (Code Design for Better Development Experience)

Target: `src/demo6_devui.py` and `entities/**`

This demo is not about "running an agent" but
serves as the entry point for **hosting entities/workflows as a "touchable UI" during development**.

The essence of DevUI is not "LLM performance" but:

- Reducing friction to "launch and try" an entity
- Quickly identifying the cause when something fails

—building **developer experience (DX)** through code.

### Reading Order for This File (A Route That Avoids Getting Lost)

1. The process of adding `repo_root` to `sys.path`
   - Why it is needed (import issues from running `python src/...` directly)
2. Entity import: `from entities.event_planning_workflow.workflow import workflow`
   - Reveals the design of "what happens at import time / where to validate"
3. Env variables that change DevUI behavior: `DEMO_NO_OPEN`, `DEVUI_HOST`, `DEVUI_PORT`
4. Port pre-check (socket bind)
   - "Fails more clearly than a Uvicorn error"
5. `serve(entities=[workflow], host=..., port=..., auto_open=...)`
   - The final call to start DevUI

### 1) `sys.path` Adjustment: Avoid "Relative Import Hell" with `python src/demo6_devui.py`

This demo executes a file directly from `src/`.
In that case, `sys.path[0]` tends to be `src/`, making `entities/` at the repository root unimportable.

To fix this, the following processing is added to **include the repo root in the import path**:

- `repo_root = Path(__file__).resolve().parents[1]`
- `sys.path.insert(0, str(repo_root))`

This "small consideration" is extremely important as the entry point for DevUI.
It preemptively eliminates the "can't import" problem that beginners commonly struggle with.

### 2) Entity Import: DevUI Starts from "Importing and Passing an Entity"

`demo6_devui.py` imports the entity to pass to DevUI with:

- `from entities.event_planning_workflow.workflow import workflow`

The key takeaway here is that DevUI
**assumes "import succeeds first"**.

DevUI loads entities for listing/launching.
Therefore, on the entity side, the effective design is:

- Do not crash with heavy processing or required config checks at import time (= don't die before the UI)
- Fail-fast at runtime for conditions required for execution

This demo chooses `entities/event_planning_workflow/workflow.py`
precisely because it embodies this "separation design" (see comparison at the bottom of the guide).

### 3) Env Variables for DevUI Behavior: "Adapt auto-open and host/port to the Environment"

This demo allows adjusting whether to open the UI, and the listening host/port via env:

- `DEMO_NO_OPEN`
  - If `1/true/yes`, then `auto_open=False`
  - A switch to "not automatically open a browser" in Codespaces/CI/headless environments
- `DEVUI_HOST` (default `0.0.0.0`)
  - Ensures accessibility in Dev Container and port-forwarding environments
- `DEVUI_PORT` (default `8081`)
  - As noted in the comments, `8080` is often used by other tools and prone to "conflicts/instability"

This is not about "how to use DevUI" but about
the design of **providing both "working defaults" and "escape hatches for environment differences" simultaneously**.

### 4) Port Pre-Check: Stop "Clearly" Before Startup

Before `serve(...)`, a socket is used to check whether
`(host, port)` can be bound.

- If `errno == 98` (address already in use):
  - Raise a `RuntimeError` that includes:
    - "Why it cannot start"
    - "How to fix it" (stop the existing process / change `DEVUI_PORT`)

Uvicorn's error message also reveals the cause,
but beginners often struggle with "where in the log to look."
This demo **creates the UX before startup** to reduce investigation cost.

### 5) `serve(entities=[workflow], ...)`: The Responsibility of Starting DevUI Is Consolidated Here

Finally, `agent_framework.devui.serve` is called:

- `entities=[workflow]`
  - Explicitly specify the entities to show in DevUI (this demo limits it to one)
- `host`, `port`
  - Listening configuration
- `auto_open=not no_open`
  - Convenient for local development, disabled for headless

Through the design up to this point:

- Entity import issues
- Startup port conflicts
- Auto-open environment differences

—these "stumbling blocks before DevUI" have been reduced.

### For Practical Application (Mapping to Real Development)

- Showing multiple entities in DevUI
  - Before expanding to `entities=[workflow1, workflow2, ...]`,
    **make ensuring each entity does not crash on import the top priority**
- Using DevUI with a team
  - Maintain the env-based host/port approach (this demo's pattern) and clearly indicate "what to change" in the README/guide
- Making entity validation safer
  - Keep imports light; fail-fast at runtime with a function like `_validate_environment()`
  - Separate DevUI listing and execution requirements

### Entity Variations (Understanding What Runs in DevUI)

`entities/**` contains multiple workflow entities. In DevUI, **prerequisites differ depending on which entity you open**, so
first check "which client (Azure AI Foundry / Azure OpenAI) each entity uses."

- `entities/event_planning_workflow/workflow.py`
  - Uses `AzureAIAgentClient` (Azure AI Foundry Agents)
  - Env validation is consolidated in `_validate_environment()` (does not interfere with DevUI "listing")
- `entities/ai_genius_workflow/workflow.py`
  - Uses `AzureOpenAIChatClient` (Azure OpenAI)
  - Env requirements are enforced at import time, so DevUI startup may crash if env is not set (room for improvement)

> DevUI's core development experience is "starting up and seeing the list."
> Therefore, separating import and runtime requirements is even more effective in practice than in demos.

---

## Where to Look "In Code" When Something Goes Wrong

- Missing settings (env): `_require_env(...)` in each demo
- Network/DNS: `_check_project_endpoint_dns()`
- Model name: Exception translation for `Failed to resolve model info` (Demo 2/3/4/5)
- Permissions: Translation for 403/Forbidden (especially Demo 5)
- Local dependencies: `_require_command("npx")` (Demo 3/5)
- DevUI: Port pre-check and `DEMO_NO_OPEN` branching (Demo 6)

---

## References (Microsoft Learn)

*The following may reflect the "latest" version. If behavior differs, prioritize this repository (pinned).*

- Run agent (Python)
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent?pivots=programming-language-python
- Agent tools (built-in / hosted tools)
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-tools?pivots=programming-language-python
- Structured output
  - https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/structured-output?pivots=programming-language-python
- DevUI
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/?pivots=programming-language-python
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/directory-discovery
  - https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/api-reference
