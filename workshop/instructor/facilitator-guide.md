# Facilitator Guide — Agent Framework Hands-On Workshop

> **Audience:** Instructors and facilitators running the workshop.
> **Format:** Hybrid — instructor-led concept introductions followed by self-paced exercises.
> **Duration:** ≈ 5 hours (including breaks).
> **Participants:** Experienced developers new to Microsoft Agent Framework / Azure AI.

---

## 1. Pre-Workshop Checklist

Complete **every item** before the session. A single missing prerequisite can stall half the room.

### Azure & Infrastructure

- [ ] **Azure AI Foundry project** is provisioned with a deployed chat model (e.g. `gpt-4o-mini`).
- [ ] **Model deployment name** matches what will go into `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
  - Open the Foundry portal → **Models + endpoints** → confirm the exact deployment name.
- [ ] **Bing grounding connection** is configured in the Foundry project.
  - Foundry portal → **Management → Connected resources** (or **Settings → Connections**) → **+ New connection → Grounding with Bing Search**.
  - Copy the full **connection ID** (ARM path: `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project>/connections/<name>`).
- [ ] **`az login`** works from the target environment and the correct subscription is selected (`az account show`).

### Environment & Dependencies

- [ ] **Dev Container / Codespaces** launches cleanly (or local Python 3.10+ with Node.js for `npx`).
- [ ] **`pip install -r requirements.txt`** completes without errors.
  - Pinned versions: `agent-framework==1.0.0b260123`, `agent-framework-azure-ai==1.0.0b260123`, `agent-framework-devui==1.0.0b260123`.
- [ ] **`npx`** is available: `npx --version` returns a version number.
- [ ] **`.env`** file is populated with working values for `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, and `BING_CONNECTION_ID`.

### Demo Scripts — Smoke Test

Run each solution script end-to-end and confirm output:

```bash
# Exercise 1 solution
python3 -u src/demo1_run_agent.py

# Exercise 2 solution
python3 -u src/demo2_web_search.py

# Exercise 3 solution (requires npx)
python3 -u src/demo3_hosted_mcp.py

# Exercise 4 solution
python3 -u src/demo4_structured_output.py

# Exercise 5 solution (takes 2–5 minutes)
python3 -u src/demo5_workflow_edges.py

# Exercise 6 solution (starts DevUI server — Ctrl+C after confirming)
python3 -u src/demo6_devui.py
```

### Validation Scripts — Smoke Test

Each exercise has a `check.sh` that performs syntax, structure, and TODO checks. Verify:

```bash
# These should FAIL on unmodified starters (TODOs still present):
bash workshop/exercises/ex1_run_agent/check.sh       # expect fail
bash workshop/exercises/ex2_web_search/check.sh       # expect fail
bash workshop/exercises/ex3_mcp_tool/check.sh         # expect fail
bash workshop/exercises/ex4_structured_output/check.sh # expect fail
bash workshop/exercises/ex5_workflow/check.sh          # expect fail
bash workshop/exercises/ex6_devui/check.sh             # expect fail
bash workshop/exercises/ex7_capstone/check.sh          # expect fail (no files)
```

If any check.sh passes on an unmodified starter, something is wrong with the starter file.

### Materials & Logistics

- [ ] **Share `workshop/README.md`** with participants before the session (contains prerequisites, setup steps, and agenda).
- [ ] **Prepare backup:** Have solution files (`src/demo*.py`) ready to screen-share if a live demo fails.
- [ ] **DevUI port forwarding (Codespaces):** If running in Codespaces, verify that port 8080 is forwarded and accessible. Open the **Ports** tab in VS Code and confirm the forwarded URL works in a browser.
- [ ] **Reference materials** are available:
  - `workshop/reference/links.md` — curated links to docs, specs, and related projects.
  - `workshop/reference/agent-framework-guide.md` — deep technical guide.
  - `workshop/reference/api-quick-reference.md` — API cheat sheet.

---

## 2. Workshop Timing Guide

| Time | Phase | Activity | Instructor Role | Notes |
|------|-------|----------|-----------------|-------|
| **0:00 – 0:30** | Intro & Setup | Present Agent Framework overview, verify participant environments (`az login`, `pip install`, `.env`) | **Active presentation** — slides + live demo of `demo1_run_agent.py` | Run `python3 -u src/demo1_run_agent.py` live so participants see what "working" looks like |
| **0:30 – 1:00** | Phase 1: Exercise 1 | Participants complete `ex1_run_agent` (3 TODOs) | **Circulate** — help stuck participants | Most common issue: missing/empty env vars. Have participants run `check.sh` first |
| **1:00 – 1:30** | Phase 1: Exercise 2 | Participants complete `ex2_web_search` (3 TODOs) | **Circulate** — may need to help with Bing connection setup | `BING_CONNECTION_ID` is the **#1 setup friction point**. Show the Foundry portal path on screen |
| **1:30 – 1:45** | ☕ Break | | | |
| **1:45 – 2:15** | Phase 2: Exercise 3 | Participants complete `ex3_mcp_tool` (5 TODOs) | **Circulate** — less hand-holding, encourage reading hints | `npx` issues if participants are not in Dev Container. Have `node -v` ready as a check |
| **2:15 – 2:45** | Phase 2: Exercise 4 | Participants complete `ex4_structured_output` (5 TODOs) | **Circulate** — explain `response_format` placement | `response_format` goes in `agent.run()`, **NOT** in `as_agent()` — this confuses many participants |
| **2:45 – 3:00** | ☕ Break | | | |
| **3:00 – 3:30** | Phase 3: Exercise 5 | Participants complete `ex5_workflow` (8 TODOs) | **Help with WorkflowBuilder API** — show the builder chain pattern | Takes 2–5 min per run. Warn participants about wait time before they start |
| **3:30 – 4:00** | Phase 3: Exercise 6 | Participants complete `ex6_devui` (10 TODOs across 2 files + entity) | **Verify port forwarding** in Codespaces; help with entity discovery | Two-part exercise: entity package (`starter_entity/`) + server (`starter.py`). Entity `__init__.py` is easily missed |
| **4:00 – 4:45** | Phase 4: Exercise 7 | Capstone — participants build their own agent/workflow from scratch | **Encourage creativity**, suggest challenge options, let fast participants help others | No starter code. Three challenge options (A: function tool, B: new domain workflow, C: extend event planning). It's OK if some don't finish |
| **4:45 – 5:00** | Wrap-up | Review key concepts, Q&A, share next steps and resources | **Active presentation** — summarize learning path, share `links.md` | Invite volunteers to demo their capstone if time permits |

### Timing Flexibility

- If the group is **fast**: Exercises 1–2 may take only 20 min each. Use the extra time for deeper discussion of concepts or let participants start Exercise 3 early.
- If the group is **slow**: Cut Exercise 7 short (or make it take-home) to preserve time for Exercise 5 and 6, which have the highest learning value.
- **Hard stops:** If a participant is still stuck on Exercise N after the time allocation, have them look at Hint 3 (near-complete code) or view the solution file (`src/demoN_*.py`), then move on.

---

## 3. Per-Exercise Talking Points

### Exercise 1: Run Agent (⭐)

**Intro to give (1–2 min):**
> "This is the 'hello world' of Agent Framework. You'll create a connection to Azure AI Foundry, define an agent with a name and instructions, and send it a prompt. Three TODOs, all straightforward. The key takeaway is the **3-layer architecture**: Foundry project in the cloud, environment variables in `.env`, and your Python code that wires them together."

**Key thing to demonstrate:**
Run `python3 -u src/demo1_run_agent.py` on screen. Point out:
- The agent responds with a venue plan (showing it works end-to-end).
- The `[AGENT]` and `[TOOL]` OpenTelemetry span lines (if visible).

**Common confusion:**
- `AzureCliCredential` requires `az login` first — participants forget this.
- The `async with` nesting: credential wraps client wraps agent. Show the indentation pattern.

**Time warning:** If not done by 0:50, tell them to look at Hint 3 or the solution in `src/demo1_run_agent.py`.

---

### Exercise 2: Web Search Tool (⭐)

**Intro to give (1–2 min):**
> "Now we add a tool. **Hosted tools** run server-side on Foundry — you don't write search logic, you just configure the connection. The agent decides when to search. This exercise introduces `HostedWebSearchTool` backed by Bing grounding."

**Key thing to demonstrate:**
Show the **Bing connection setup** in the Foundry portal: Management → Connected resources → Grounding with Bing Search. Show where to copy the connection ID (the full ARM path).

**Common confusion:**
- `BING_CONNECTION_ID` must be the full ARM resource path, not just the connection name.
- `additional_properties` dict structure — the `user_location` plus `**bing_props` spread.
- `tools=[web_search_tool]` — it's a list, not a single tool.

**Time warning:** If not done by 1:20, nudge toward hints. The Bing connection is the main blocker.

---

### Exercise 3: MCP Tool (⭐⭐)

**Intro to give (1–2 min):**
> "MCP — Model Context Protocol — is an open standard for connecting AI models to external tools. Unlike hosted tools that run on Foundry, MCP stdio tools run **locally** as child processes. You'll spawn a `sequential-thinking` server via `npx` and give it to your agent. This is how you integrate any local tool or service."

**Key thing to demonstrate:**
Run `npx --version` to confirm it works. Briefly explain that `npx -y @modelcontextprotocol/server-sequential-thinking` downloads and runs the MCP server.

**Common confusion:**
- `npx` not found — participants not in Dev Container need Node.js installed.
- `load_prompts=False` — not intuitive, but required for this server.
- Agent instructions **must mention** the tool by name (`"Use the sequential-thinking tool..."`) or the model won't use it.

**Time warning:** If not done by 2:05, suggest hints. The MCP setup is mechanical once `npx` works.

---

### Exercise 4: Structured Output (⭐⭐)

**Intro to give (1–2 min):**
> "When an agent is part of a pipeline — not a chatbot — you need its output in a typed, predictable format. Structured output lets you pass a Pydantic model to `agent.run()`, and the agent returns data that matches your schema. This is how you go from free-text LLM responses to machine-readable data."

**Key thing to demonstrate:**
Show the output of `src/demo4_structured_output.py` — structured fields (`Title:`, `Address:`, `Cost per person:`) vs. free-text blob.

**Common confusion:**
- **#1 issue:** Putting `response_format=VenueOptionsModel` in `.as_agent()` instead of in `agent.run()`. Emphasize: **`response_format` goes in `run()`**.
- `response.value` may be `None` on some SDK versions — the fallback pattern (`VenueOptionsModel.model_validate_json(response.text)`) is important.
- Participants forget to define **both** models (`VenueInfoModel` AND `VenueOptionsModel`).

**Time warning:** If not done by 2:35, suggest looking at the solution pattern in the README.

---

### Exercise 5: Multi-Agent Workflow (⭐⭐⭐)

**Intro to give (1–2 min):**
> "This is the big one. You'll build a 5-agent pipeline: Coordinator → Venue → Catering → Budget Analyst → Booking. Each agent has a different role and tool. The `WorkflowBuilder` connects them with edges, and `run_stream()` lets you watch each agent work in real time. This is how you build business-process workflows with AI."

**Key thing to demonstrate:**
Show the `WorkflowBuilder` chain pattern on screen:
```python
WorkflowBuilder()
  .set_start_executor(coordinator)
  .add_edge(coordinator, venue)
  .add_edge(venue, catering)
  .add_edge(catering, budget_analyst)
  .add_edge(budget_analyst, booking)
  .build()
```

**Common confusion:**
- 8 TODOs is daunting. Tell participants: "Each TODO is one agent creation or one builder call — they're repetitive once you get the pattern."
- Event handling: Three event types (`AgentRunUpdateEvent`, `ExecutorCompletedEvent`, `WorkflowOutputEvent`). Show the `isinstance` pattern.
- **Long execution time** (2–5 min) surprises participants. Warn them up front.

**Time warning:** At 3:20, tell anyone still working to use Hint 3. They need time for Exercise 6.

---

### Exercise 6: DevUI (⭐⭐⭐)

**Intro to give (1–2 min):**
> "DevUI is a development-only web UI for running and debugging your workflows visually. In this exercise you'll create an entity package — a directory with `__init__.py` that exports your workflow — and launch a DevUI server. You'll see your agents run in a browser."

**Key thing to demonstrate:**
Run `python3 -u src/demo6_devui.py` and show the web UI at `http://localhost:8080`. Point out:
- The entity listing page.
- Submitting a prompt and watching agents execute.
- The `/v1/models` API endpoint: `curl -s http://localhost:8080/v1/models | python3 -m json.tool`.

**Common confusion:**
- **Entity discovery:** The `starter_entity/` directory MUST have `__init__.py` that exports `workflow`. Missing or empty `__init__.py` = DevUI finds nothing.
- This exercise has **two parts** (entity package + server script) — participants sometimes only do one.
- The DevUI exercise uses `register_agent(factory_fn, name)` with **string names** for edges (not agent instances like Exercise 5). This difference trips people up.
- Port 8080 already in use — set `DEVUI_PORT=8081`.
- In Codespaces, need to forward port in the Ports tab and use the forwarded URL.

**Time warning:** At 3:55, if not done, have them look at the solution (`src/demo6_devui.py` + `entities/event_planning_workflow/`).

---

### Exercise 7: Capstone (⭐⭐⭐⭐)

**Intro to give (1–2 min):**
> "No starter code, no TODOs — you build from scratch. Choose one of three challenges: (A) custom function tool + agent, (B) new domain multi-agent workflow, or (C) extend the event planning system. Use everything you've learned. It's OK if you don't finish — the goal is to design and start building."

**Key thing to demonstrate:**
Show the boilerplate skeleton from the Exercise 7 README — the `.env` loading, `_require_env()`, and `async def main()` pattern. Remind them to copy these from any starter file.

**Common confusion:**
- Participants freeze at the blank page. Suggest: "Start by listing your agents and their roles in a comment block. Then copy the boilerplate from Exercise 1's starter."
- Some try to build something too ambitious. Encourage starting with a single working agent, then layering on.

**Time warning:** At 4:35, invite anyone who has something working to demo. Remind everyone they can continue after the workshop.

---

## 4. Common Participant Issues — Triage Guide

When a participant raises their hand, match the error to the resolution below.

### Issue 1: `RuntimeError: Required environment variable is missing or empty`

**Cause:** `.env` file missing or incomplete.

**Resolution:**
```bash
# Check .env exists and has values
cat .env

# Verify the critical variables
echo "ENDPOINT: $AZURE_AI_PROJECT_ENDPOINT"
echo "MODEL: $AZURE_AI_MODEL_DEPLOYMENT_NAME"
echo "BING: $BING_CONNECTION_ID"

# If empty, copy from template and fill in
cp .env.example .env
# Then edit .env with actual values
```

Also check: `az login` may have expired. Run `az account show` — if it fails, re-run `az login --use-device-code`.

---

### Issue 2: `Cannot resolve DNS` / connection timeout

**Cause:** Azure AI Foundry endpoint is unreachable — typically a private networking / private DNS issue.

**Resolution:**
- Check the endpoint URL: `echo $AZURE_AI_PROJECT_ENDPOINT`
- Try a DNS lookup: `nslookup <host-from-endpoint>`
- If it fails: the Foundry project uses **Private Link** and the current network can't resolve the private DNS.
- **Fix:** Use a different Foundry project with a **public endpoint**, or ensure the network can resolve `*.services.ai.azure.com`.

---

### Issue 3: `Failed to resolve model info`

**Cause:** The value in `AZURE_AI_MODEL_DEPLOYMENT_NAME` doesn't match any deployment in the Foundry project.

**Resolution:**
- Open the Foundry portal → **Models + endpoints** → confirm the **exact** deployment name.
- Common mistakes: using the model name (`gpt-4o-mini`) instead of the deployment name (`gpt-4o-mini-deploy`), or extra whitespace.

---

### Issue 4: `401 Unauthorized` / `403 Forbidden`

**Cause:** Azure CLI token expired or insufficient RBAC permissions.

**Resolution:**
```bash
# Re-authenticate
az login --use-device-code

# Verify correct subscription
az account show --query "{name:name, id:id}" -o table

# If wrong subscription
az account set --subscription "<correct-subscription-id>"
```

If RBAC is the issue: the participant needs at least **Cognitive Services User** (or equivalent) role on the Foundry project resource.

---

### Issue 5: `npx: command not found` (Exercise 3)

**Cause:** Node.js / npm not installed. This happens when participants are **not** using the Dev Container.

**Resolution:**
```bash
# Check if Node.js is available
node --version
npx --version

# If not, and using Dev Container — reopen in container
# If running locally, install Node.js:
#   macOS: brew install node
#   Ubuntu: sudo apt install nodejs npm
#   Or: https://nodejs.org/
```

---

### Issue 6: Bing connection errors (Exercise 2+)

**Cause:** `BING_CONNECTION_ID` not set, empty, or wrong format.

**Resolution:**
- The value must be the **full ARM resource path**, not just the connection name.
- Format: `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project>/connections/<connection-name>`
- Find it in: Foundry portal → **Management → Connected resources** → click on the Bing connection → copy the **Resource ID** or **Connection ID**.
- If the connection doesn't exist: walk the participant through creating it (portal → Connected resources → + New → Grounding with Bing Search).

---

### Issue 7: `response.value` is `None` (Exercise 4)

**Cause:** SDK version difference — some versions populate `.value`, others return JSON in `.text`.

**Resolution:**
This is expected. The exercise README includes a fallback pattern:
```python
venue_options = response.value
if venue_options is None:
    venue_options = VenueOptionsModel.model_validate_json(response.text)
```
If the participant didn't implement the fallback, point them to the hint or the solution in `src/demo4_structured_output.py`.

---

### Issue 8: `Port already in use` (Exercise 6)

**Cause:** Another process (previous DevUI run, or another service) is listening on port 8080.

**Resolution:**
```bash
# Find what's using the port
lsof -i :8080

# Kill it (replace <PID> with actual PID)
kill <PID>

# Or use a different port
export DEVUI_PORT=8081
python3 -u workshop/exercises/ex6_devui/starter.py
```

---

### Issue 9: `ModuleNotFoundError: No module named 'agent_framework'`

**Cause:** Dependencies not installed.

**Resolution:**
```bash
pip install -r requirements.txt
```

If inside a Dev Container and it still fails, try:
```bash
pip install --force-reinstall -r requirements.txt
```

---

### Issue 10: Entity not detected by DevUI (Exercise 6)

**Cause:** The entity package structure is incorrect.

**Resolution checklist:**
1. Does `starter_entity/__init__.py` exist?
2. Does it contain `from .workflow import workflow`?
3. Does `starter_entity/workflow.py` define a variable named `workflow`?
4. Does the `serve()` call pass `entities=[workflow]`?

```bash
# Quick structural check
cat workshop/exercises/ex6_devui/starter_entity/__init__.py
# Should output: from .workflow import workflow

# Run the exercise check script
bash workshop/exercises/ex6_devui/check.sh
```

Show them the working example in `entities/event_planning_workflow/` as a reference.

---

## 5. Pacing Advice

### If Participants Are Ahead

- Point them to the **Bonus Challenges** listed at the end of each exercise README.
- Suggest they try combining concepts (e.g., add structured output to Exercise 3, or add MCP to Exercise 2).
- Let fast finishers **help slower participants** — peer teaching reinforces learning.
- Encourage them to read `workshop/reference/agent-framework-guide.md` for deeper understanding.

### If Participants Are Behind

- **Hint system:** Each exercise README has progressive hints — Hint 1 (concept nudge), Hint 2 (more specific), Hint 3 (near-complete code). Encourage participants to use them.
- **Solution files:** If a participant is more than 10 minutes behind, suggest they read the solution file (`src/demoN_*.py`), understand it, then type the key parts themselves.
- **Don't let anyone fall more than one exercise behind.** If they're stuck on Exercise 2 when the group is on Exercise 4, pair them with a fast participant or walk them through the solution directly.

### If the Majority Is Stuck on the Same Issue

- **Stop and do a group demo.** Project your screen and walk through the solution step by step.
- This is most likely to happen with:
  - `.env` / environment variable setup (Intro & Setup)
  - Bing connection ID (Exercise 2)
  - `response_format` placement (Exercise 4)
  - WorkflowBuilder pattern (Exercise 5)
  - Entity discovery (Exercise 6)

### Phase 4 (Capstone) Is Intentionally Flexible

- Some participants won't finish — **that's OK**. The goal is to design and start building, not to complete a polished solution.
- Tell participants upfront: "You can continue this after the workshop. The repo and your Codespace will still be available."
- If time is running short, cut the capstone to 30 min and use the last 15 min for Q&A and demos.

### General Pacing Rules

- **Never skip Exercise 5** — it's the most impactful for understanding multi-agent orchestration.
- **Exercise 6 (DevUI)** can be shortened by having participants look at the solution entity (`entities/event_planning_workflow/`) rather than building from scratch.
- **Exercise 7 (Capstone)** is the first thing to shorten if time is tight.

---

## 6. Environment Variations

### GitHub Codespaces (Recommended)

- All tools are pre-configured (Python 3.11+, Node.js, `npx`, pip packages).
- **Authentication:** Use `az login --use-device-code` (headless environment — no browser popup).
- **DevUI port forwarding:** When DevUI starts on port 8080, Codespaces auto-detects and forwards it. Find the URL in the **Ports** tab of VS Code or the Codespaces browser IDE.
  - If the port doesn't appear, manually forward: Ports tab → **Add Port** → 8080.
  - Share the forwarded URL (looks like `https://<codespace-name>-8080.app.github.dev`) with participants who are testing the DevUI API.
- **Browser auto-open won't work** in Codespaces. Participants must click the forwarded URL or set `DEMO_NO_OPEN=1`.

### Local Dev Container (VS Code)

- Same as Codespaces, but runs on the participant's machine.
- **No port forwarding needed** — `localhost:8080` works directly.
- **Authentication:** `az login` works with a browser popup (not headless).
- Potential issue: Docker not running → "Cannot connect to Docker daemon." Fix: start Docker Desktop.

### No Dev Container (Bare Metal / Vanilla Python)

- Participants must manually install:
  - **Python 3.10+** (3.11+ recommended)
  - **Node.js** (for `npx` in Exercise 3)
  - `pip install -r requirements.txt`
  - Azure CLI (`az`)
- **Common issues:**
  - Wrong Python version (`python3 --version` < 3.10 → type hint syntax errors).
  - Missing `npx` → Exercise 3 will fail. Provide instructions: `brew install node` (macOS), `sudo apt install nodejs npm` (Ubuntu), or download from [nodejs.org](https://nodejs.org/).
  - Virtual environment confusion — suggest: `python3 -m venv .venv && source .venv/bin/activate`.

---

## 7. Post-Workshop

### Immediate Follow-Up

- **Share reference links:** Point participants to `workshop/reference/links.md` for official docs, API references, and related projects.
- **Deeper learning:** Recommend `workshop/reference/agent-framework-guide.md` for a comprehensive technical guide covering architecture, MCP deep dive, A2A overview, and production considerations.
- **API cheat sheet:** `workshop/reference/api-quick-reference.md` is a handy reference for common API patterns.

### Encourage Continued Exploration

- "Try different prompts and domains" — the event planning scenario is just a starting point.
- Participants can continue working in their Codespace after the workshop (Codespaces persist for a configurable retention period).
- Suggest extending the capstone project or trying the bonus challenges they skipped.

### Collect Feedback

- Ask for feedback on:
  - Pacing (too fast / too slow / about right)
  - Exercise difficulty curve
  - Most valuable exercise
  - Biggest pain point
  - What they'd want in a follow-up workshop
- Feedback helps calibrate timing and identify environment issues for future sessions.

### Useful Links to Share

| Resource | URL |
|----------|-----|
| Agent Framework overview | <https://learn.microsoft.com/azure/ai-foundry/agent-framework/overview> |
| Azure AI Foundry Agents | <https://learn.microsoft.com/azure/ai-services/agents/overview> |
| MCP specification | <https://modelcontextprotocol.io/> |
| Agent Framework GitHub | <https://github.com/microsoft/agent-framework> |
| This workshop repo | *(share your repo URL)* |

> **Note:** Microsoft Learn docs may reference the latest SDK version. This workshop uses pinned version `1.0.0b260123`. If docs and workshop code diverge, the workshop code is correct for this session.
