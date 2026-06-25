# Workshop Validation Walkthrough

**Date:** June 25, 2026  
**Status:** Draft — needs revisit before June 30 workshop  

---

## Module 1: Kiro Setup (15 min)

**What participants do:**
1. Open the pre-cloned `aa-workshop-agent` repo in Kiro
2. Install three Powers (aws-agentcore, strands, cloud-architect)
3. Run `uv sync` or `pip install -e .`
4. Run `aws sts get-caller-identity` + verify Nova model access

**How Kiro accelerates:**
- Powers auto-surface relevant docs inline as participants write code later — no tab-switching to AWS docs
- The steering file (`aa-workshop.md`) is already in `.kiro/steering/`, so Kiro has project context from the moment they open it

**Potential friction:**
- If Bedrock Nova Pro isn't enabled in their region, participants hit a wall. The troubleshooting section covers this, but we should verify access *before* the workshop day. Consider a pre-flight script.
- `uv` may not be installed on all machines. We have `pip install -e .` as fallback, but should we just standardize on pip for simplicity?

---

## Module 2: Spec-Driven Planning (30 min)

**What participants do:**
1. Open `.kiro/specs/aa-workshop-agent/requirements.md` — read through it
2. In Kiro chat, click "Generate Tech Design" → Kiro generates `design.md`
3. Click "Generate Task List" → Kiro generates `tasks.md`

**How Kiro accelerates:**
- This is the headline demo of Kiro's value. Participants go from written requirements to a full technical design and ordered implementation plan in ~5 minutes of actual Kiro execution
- The design will reference the dual-mode pattern, graph client, tools architecture — all derived from the requirements we wrote
- Tasks come out pre-ordered with dependencies

**Potential friction:**
- The requirements document is already written (we authored it). Participants aren't writing requirements from scratch — they're reviewing them. Is that okay for the learning objective? I think yes — it shows the *output* of spec-driven development. If we want them to experience authoring, we could have them add a requirement (e.g., "add a weather delay tool") and regenerate.
- Generated design/tasks may not perfectly match the code examples in the guide. We should run this end-to-end once beforehand and verify alignment, or accept minor differences as "Kiro's interpretation."

---

## Module 3: Build the Agent (45 min)

**What participants do:**
1. Create `src/data_store.py` — load JSON
2. Create `src/tools.py` — three @tool functions + find_connections
3. Create `src/graph_client.py` — NetworkX LocalGraphClient
4. Create `src/agent.py` — agent with Nova Pro, system prompt, tools list

**How Kiro accelerates:**
- With the `strands` power active, Kiro has context on @tool decorator patterns, docstring requirements, and error handling conventions
- With the steering file loaded, Kiro knows the project structure, coding style (Google docstrings, type annotations, no classes unless needed)
- Participants can ask Kiro to generate each file from the task list — Kiro references the design.md to produce code that matches the architecture
- If someone gets stuck on the graph client, they can ask Kiro "how does NetworkX find all simple paths?" and the cloud-architect power provides context

**Potential friction:**
- This is the longest module and the most code. 45 minutes is tight for typing. Consider: should the data_store.py and graph_client.py be pre-built (since they're infrastructure), letting participants focus on tools.py and agent.py (the learning)?
- The routes.json file needs to exist in `data/`. Is it pre-populated in the repo, or do participants create it? It should be pre-populated.
- Import paths (`from src.data_store import FLIGHTS`) require the project to be installed or `PYTHONPATH` set. The `pip install -e .` handles this, but it's a common gotcha.

---

## Module 4: Test Locally (20 min)

**What participants do:**
1. Create `src/entrypoint_local.py` — FastAPI wrapper
2. Run `RUNTIME_MODE=local python -m src.entrypoint_local`
3. In a new terminal, run `python cli.py`
4. Test 4 queries including the Dallas disruption scenario
5. Test with curl

**How Kiro accelerates:**
- If the agent produces unexpected responses, participants can paste the output into Kiro chat and ask "why did the agent not call find_connections?" — Kiro can analyze the system prompt and tool docstrings
- The steering file's "Common Pitfalls" section is surfaced if they hit port conflicts or connection errors

**Potential friction:**
- Opening a second terminal is a step some participants fumble with. Clear instruction needed.
- The Dallas disruption query depends on the data in flights.json/routes.json being correct (AA456 delayed, AA789 departing 15:45, alternatives available). If the data doesn't match, the demo falls flat. This is the most critical data dependency.
- How does `cli.py` work? It POSTs to localhost:8001/invocations. Is it pre-built in the repo? It should be.
- The agent response quality depends on Nova Pro's tool-use capability. We should test this specific model + prompt combination beforehand to ensure it reliably calls find_connections with exclude_hub="DFW" rather than just calling search_flights.

---

## Module 5: Run Tests (15 min)

**What participants do:**
1. Run `pytest tests/ -v`
2. Review test patterns in `test_tools.py`

**How Kiro accelerates:**
- If tests fail, participants paste the error into Kiro and it diagnoses the issue
- Kiro can generate additional test cases if asked ("write a test for find_connections when no path exists")

**Potential friction:**
- Tests need to be pre-written in the repo. Are they? If not, this module becomes "write tests" which is a different (longer) activity.
- Tests should pass before deployment. If there's a bug, we need buffer time here.

---

## Module 6: Deploy to AWS (30 min)

**What participants do:**
1. Create `src/entrypoint_aws.py` — BedrockAgentCoreApp wrapper
2. Run `cdk bootstrap` (if needed)
3. Run `cdk deploy`
4. Wait 5-10 min
5. Test with `aws bedrock-agentcore invoke-agent-runtime`

**How Kiro accelerates:**
- The `aws-agentcore` power provides deployment guidance if participants hit errors
- The `cloud-architect` power helps with CDK construct documentation if they want to understand what's being provisioned
- Kiro can explain the CDK output (endpoint URL, resource ARNs)

**Potential friction:**
- CDK bootstrap can fail if the account/region hasn't been bootstrapped before. This is a one-time operation that needs admin permissions.
- 5-10 min deployment wait is dead time. What do participants do? Suggestion: use this time for a guided discussion about the dual-mode pattern and what AgentCore is doing under the hood.
- The `deployment/cdk_app.py` needs to exist and be correct. Is it pre-built? It should be — writing a CDK stack from scratch in 30 min isn't feasible.
- IAM permissions: the deploying user needs broad permissions (CDK bootstrap role). If participants are in a restricted workshop account, this could fail.

---

## Module 7: Explore Gateway (20 min)

**What participants do:**
1. Navigate to AWS Console → Bedrock → AgentCore → Gateway
2. Find the "flight-operations" target
3. View registered tools and their schemas
4. Discuss access policies

**How Kiro accelerates:**
- Kiro can explain what they're seeing in the console if they get lost
- The `aws-agentcore` power provides context on MCP protocol and access policy enforcement

**Potential friction:**
- This is a console-exploration module, not a coding module. Some participants may find it passive. Consider: have them modify an access policy (deny find_connections to the Flight_Ops_Agent) and observe the error.
- Console UI for AgentCore Gateway may change. Screenshots in the guide would go stale. Keep instructions action-based ("navigate to...") rather than screenshot-dependent.

---

## Module 8: Observability (15 min)

**What participants do:**
1. Enable CloudWatch Transaction Search (if not already done)
2. Invoke the deployed agent 3 times
3. Wait 2-3 min
4. View session metrics in CloudWatch GenAI Observability dashboard
5. Drill into a trace
6. Exercise: identify the slowest span

**How Kiro accelerates:**
- The `aws-agentcore` power can explain trace/span concepts if participants are unfamiliar
- If traces don't appear, Kiro can help troubleshoot (Transaction Search not enabled, IAM permissions missing)

**Potential friction:**
- The 2-3 min wait for telemetry propagation is awkward in a live workshop. Suggestion: have them invoke the agent in Module 6 testing, so by the time they reach Module 8, traces are already available.
- CloudWatch GenAI Observability dashboard is relatively new UI. If it's not immediately obvious where to find it, participants may get stuck. Consider: provide the direct URL pattern.
- 15 min is tight for enabling Transaction Search + generating telemetry + exploring. If Transaction Search is already enabled (pre-workshop setup), this works. If not, add 5 min.

---

## Overall Kiro Acceleration Story

| Without Kiro | With Kiro |
|---|---|
| Read AWS docs in browser tabs to understand @tool decorator, AgentCore deployment, CDK constructs | Powers surface docs inline as you code |
| Write requirements, design, tasks manually | Generate design + tasks from requirements in minutes |
| Debug tool invocation issues by reading Strands source code | Ask Kiro "why didn't the agent call this tool?" |
| Look up CDK construct syntax in docs | Kiro suggests constructs from cloud-architect power |
| Context-switch between docs, IDE, and terminal | Everything stays in one environment |
| Manually trace through agent reasoning | Kiro explains tool call chains from traces |

**The 30-minute spec planning module is the biggest acceleration demo.** Going from requirements → design → tasks in 5 minutes of Kiro execution (the rest is review time) is the moment that lands with leadership.

---

## Pre-Workshop Checklist (for us)

- [ ] Verify Nova Pro tool-use works reliably with the Dallas disruption prompt
- [ ] Pre-populate: `data/flights.json`, `data/routes.json`, `cli.py`, `tests/test_tools.py`, `deployment/cdk_app.py`, `pyproject.toml`
- [ ] Run `cdk deploy` end-to-end in the target account to verify it works
- [ ] Enable CloudWatch Transaction Search in the workshop account
- [ ] Verify the flights.json has the AA456 delay + AA789 connection + alternative routes data
- [ ] Test the full Dallas disruption scenario locally and confirm the agent calls find_connections with exclude_hub
- [ ] Decide: `uv sync` vs `pip install -e .` — pick one and standardize
- [ ] Time the full workshop yourself — does it actually fit in 3 hours?
- [ ] Pre-bootstrap CDK in the workshop account
- [ ] Prepare a "dead time" discussion script for the 5-10 min CDK deploy wait
- [ ] Confirm workshop AWS account has Bedrock, AgentCore, Neptune (if showing Module 10) access
